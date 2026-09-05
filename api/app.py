"""Minimal Haji HTTP API for the mobile client and safe trading analysis."""
from __future__ import annotations
import base64, binascii, hmac, json, os
from dataclasses import asdict
from datetime import datetime
from email.parser import BytesParser
from email.policy import default
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from uuid import uuid4
from core.agent import HajiAgent
from core.ai_provider import provider_from_env
from core.approval_store import PersistentApprovalStore
from core.module_bootstrap import build_default_registry
from core.models import ApprovalRequest, RiskLevel
from core.notifications import NotificationService
from core.persistent_memory import PersistentMemoryStore
from core.runtime import HajiRuntime, RuntimeEvent
from core.tasks import TaskManager
from modules.notifications.mobile import MobileNotificationInbox
from modules.trading import ApprovedTrade, BinancePublicMarketData, PaperBroker, TradeCandidate, TradingApprovalBridge, TradingService
MAX_BODY_BYTES=max(1024,int(os.getenv("HAJI_MAX_BODY_BYTES",str(10*1024*1024))))
class HajiApp:
    def __init__(self):
        self.runtime=HajiRuntime(); self.modules=build_default_registry(); db=os.getenv("HAJI_MEMORY_DB","haji_memory.sqlite3")
        self.memory=PersistentMemoryStore(db); self.approvals=PersistentApprovalStore(db,ttl_seconds=max(60,int(os.getenv("HAJI_APPROVAL_TTL_SECONDS","900"))))
        self.tasks=TaskManager(runtime=self.runtime); self.notifications=NotificationService(self.runtime); self.mobile_notifications=MobileNotificationInbox()
        self.notifications.register(lambda n:self.mobile_notifications.push({"title":n.title,"message":n.message,"level":n.level,"created_at":n.created_at.isoformat(),"metadata":n.metadata}))
        self.provider=provider_from_env(); self.agent=HajiAgent(memory=self.memory,tasks=self.tasks,runtime=self.runtime,provider=self.provider)
        self.trading_approvals=TradingApprovalBridge(); self.trading_provider=BinancePublicMarketData(base_url=os.getenv("HAJI_MARKET_DATA_URL","https://api.binance.com"),interval=os.getenv("HAJI_MARKET_INTERVAL","1m"))
        self.trading=TradingService(self.trading_provider,approvals=self.trading_approvals); self.paper_broker=PaperBroker(); self.runtime.start()
    def message(self,text,image=None): return self.agent.handle(text=text,image=image)
    def approve(self,approval_id): return self.agent.approve(approval_id)
    def trading_analyze(self,symbols,limit=200):
        result=[]
        for opportunity in self.trading.analyze(symbols,limit=limit):
            approval_id=uuid4().hex; self.approvals.put(approval_id,opportunity.approval.action,opportunity.approval.risk.value,opportunity.approval.reason,asdict(opportunity.candidate))
            result.append({"approvalId":approval_id,"candidate":asdict(opportunity.candidate),"approval":asdict(opportunity.approval)})
        return {"ok":True,"opportunities":result,"count":len(result),"mode":"paper_only"}
    def trading_approve(self,approval_id):
        record=self.approvals.consume(approval_id)
        if record is None:return {"ok":False,"error":"trading_approval_not_found_or_expired"}
        try:
            candidate=TradeCandidate(**record["payload"]); request=ApprovalRequest(action=record["action"],risk=RiskLevel(record["risk"]),reason=record["reason"],created_at=datetime.fromisoformat(record["created_at"]),approved=False)
            executed=self.paper_broker.execute(ApprovedTrade(candidate,self.trading_approvals.approve(request)))
        except Exception as exc:return {"ok":False,"error":"trading_execution_failed","detail":str(exc)}
        self.runtime.emit(RuntimeEvent("trading.paper_executed",{"approval_id":approval_id,"symbol":candidate.symbol})); return {"ok":True,"approvalId":approval_id,"execution":asdict(executed)}
app=HajiApp()
class Handler(BaseHTTPRequestHandler):
    def _cors_origin(self): return os.getenv("HAJI_CORS_ORIGIN","*")
    def _json(self,status,payload):
        data=json.dumps(payload,ensure_ascii=False,default=str).encode(); self.send_response(status); self.send_header("Content-Type","application/json; charset=utf-8"); self.send_header("Content-Length",str(len(data))); self.send_header("Access-Control-Allow-Origin",self._cors_origin()); self.send_header("Access-Control-Allow-Headers","Content-Type, Authorization, X-Haji-API-Key"); self.end_headers(); self.wfile.write(data)
    def _authorized(self):
        expected=os.getenv("HAJI_API_TOKEN","");
        if not expected:return True
        auth=self.headers.get("Authorization",""); supplied=auth[7:].strip() if auth.lower().startswith("bearer ") else self.headers.get("X-Haji-API-Key",""); return bool(supplied) and hmac.compare_digest(supplied,expected)
    def _require_auth(self):
        if self.path.startswith("/v1/") and not self._authorized(): self._json(401,{"error":"unauthorized"}); return False
        return True
    def _read_body(self):
        try:length=int(self.headers.get("Content-Length","0"))
        except ValueError:length=0
        if length<0:self._json(400,{"error":"invalid_content_length"}); return b""
        if length>MAX_BODY_BYTES:self._json(413,{"error":"request_too_large","max_bytes":MAX_BODY_BYTES}); return b""
        return self.rfile.read(length)
    def _parse_multipart(self,raw,content_type):
        msg=BytesParser(policy=default).parsebytes(f"Content-Type: {content_type}\r\nMIME-Version: 1.0\r\n\r\n".encode()+raw); fields={}
        if msg.is_multipart():
            for part in msg.iter_parts():
                name=part.get_param("name",header="content-disposition")
                if name:fields[name]=part.get_payload(decode=True) or b""
        return fields
    @staticmethod
    def _decode_image(encoded):
        if not encoded:return None
        value=str(encoded); value=value.split(",",1)[1] if ";base64," in value else value
        try:return base64.b64decode(value,validate=True)
        except (ValueError,binascii.Error):raise ValueError("invalid_image_base64") from None
    def do_POST(self):
        if not self._require_auth():return
        if self.path.startswith("/v1/agent/approval/"):self._json(200,app.approve(self.path.rsplit("/",1)[-1]));return
        if self.path.startswith("/v1/trading/approval/"):self._json(200,app.trading_approve(self.path.rsplit("/",1)[-1]));return
        if self.path=="/v1/trading/analyze":
            raw=self._read_body()
            try:
                body=json.loads(raw.decode()) if raw else {}; symbols=body.get("symbols",[]); limit=int(body.get("limit",200));
                if not isinstance(symbols,list) or not symbols:raise ValueError("symbols_required")
                self._json(200,app.trading_analyze([str(s) for s in symbols],limit))
            except ValueError as exc:self._json(400,{"error":"trading_analysis_failed","detail":str(exc)})
            except Exception:self._json(502,{"error":"trading_analysis_failed"})
            return
        if self.path=="/v1/agent/voice":
            raw=self._read_body()
            if not raw and self.headers.get("Content-Length","0") not in ("0",""):return
            try:
                fields=self._parse_multipart(raw,self.headers.get("Content-Type","")) if "multipart/form-data" in self.headers.get("Content-Type","") else {"audio":raw}; audio=fields.get("audio",b"")
                if not audio:raise ValueError("empty_audio")
                if app.provider is None:self._json(503,{"error":"ai_provider_not_configured","text":"الصوت وصل، لكن مزود الذكاء مش مفعّل على السيرفر."});return
                transcript=app.provider.transcribe(audio,"audio/mp4"); self._json(200,{**app.message(transcript),"transcript":transcript})
            except ValueError:self._json(400,{"error":"audio_required"})
            except NotImplementedError:self._json(501,{"error":"transcription_not_implemented"})
            except Exception:self._json(502,{"error":"transcription_failed"})
            return
        if self.path!="/v1/agent/message":self._json(404,{"error":"not_found"});return
        raw=self._read_body(); content_type=self.headers.get("Content-Type",""); text=""; image=None
        try:
            if "application/json" in content_type:
                body=json.loads(raw.decode()); text=str(body.get("text","")); image=self._decode_image(body.get("image"))
            elif "multipart/form-data" in content_type:
                fields=self._parse_multipart(raw,content_type); text=fields.get("text",b"").decode("utf-8",errors="replace"); image=fields.get("image")
            else:self._json(415,{"error":"unsupported_content_type"});return
        except (ValueError,UnicodeDecodeError):self._json(400,{"error":"invalid_json_or_image"});return
        self._json(200,app.message(text,image))
    def do_GET(self):
        if self.path=="/health":self._json(200,{"status":"ok","provider_configured":app.provider is not None,"market_data":"binance_public","trading_mode":"paper_only"});return
        if not self._require_auth():return
        if self.path=="/v1/notifications":self._json(200,{"ok":True,"notifications":app.mobile_notifications.list()});return
        if self.path=="/v1/runtime/status":self._json(200,{**app.runtime.status(),"modules":app.modules.capabilities()});return
        if self.path=="/v1/modules":self._json(200,{"ok":True,"modules":app.modules.capabilities()});return
        self._json(404,{"error":"not_found"})
    def do_OPTIONS(self):
        self.send_response(204); self.send_header("Access-Control-Allow-Origin",self._cors_origin()); self.send_header("Access-Control-Allow-Methods","GET, POST, OPTIONS"); self.send_header("Access-Control-Allow-Headers","Content-Type, Authorization, X-Haji-API-Key"); self.end_headers()
def run(host="0.0.0.0",port=8000):
    print(f"Haji API listening on http://{host}:{port}"); ThreadingHTTPServer((host,port),Handler).serve_forever()
if __name__=="__main__":run()
