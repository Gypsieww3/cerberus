"""Local Ollama gateway; no code execution, redirects or non-loopback endpoints."""
import json
from urllib import request, error
from urllib.parse import urlsplit

class GatewayError(RuntimeError):
    pass

class OllamaGateway:
    def __init__(self, endpoint="http://127.0.0.1:11434", timeout=20):
        parsed=urlsplit(endpoint)
        if parsed.scheme!="http" or parsed.hostname not in {"localhost","127.0.0.1","::1"} or parsed.username or parsed.password or parsed.query or parsed.fragment or parsed.path.strip("/"):
            raise ValueError("Endpoint must be a local HTTP origin")
        if isinstance(timeout,bool) or not isinstance(timeout,(int,float)) or not 0<timeout<=120:
            raise ValueError("Invalid timeout")
        self.endpoint=endpoint.rstrip("/")
        self.timeout=timeout
    def generate(self, model, prompt, max_tokens=256):
        if not isinstance(model,str) or not 1<=len(model)<=100 or any(c in model for c in "\r\n\t /"):
            raise ValueError("Invalid model")
        if not isinstance(prompt,str) or not 1<=len(prompt)<=12000:
            raise ValueError("Invalid prompt length")
        if type(max_tokens) is not int or not 1<=max_tokens<=2048:
            raise ValueError("Invalid token limit")
        data=json.dumps({"model":model,"prompt":prompt,"stream":False,
                         "options":{"num_predict":max_tokens}}).encode("utf-8")
        req=request.Request(self.endpoint+"/api/generate",data=data,method="POST",
                            headers={"Content-Type":"application/json"})
        class NoRedirect(request.HTTPRedirectHandler):
            def redirect_request(self, req, fp, code, msg, headers, newurl):
                raise GatewayError("Redirect denied")
        opener=request.build_opener(request.ProxyHandler({}),NoRedirect())
        try:
            with opener.open(req,timeout=self.timeout) as response:
                payload=response.read(2_000_001)
            if len(payload)>2_000_000:
                raise GatewayError("Response too large")
            output=json.loads(payload).get("response")
            if not isinstance(output,str):
                raise GatewayError("Missing generated response")
            return output
        except (error.URLError,TimeoutError,OSError,UnicodeError,json.JSONDecodeError) as exc:
            raise GatewayError(f"Local Ollama failure: {type(exc).__name__}") from exc
