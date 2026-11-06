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

    def list_models(self):
        """Fetch model tags from the local Ollama API; performs no generation."""
        req = request.Request(self.endpoint + "/api/tags", method="GET",
                              headers={"Accept": "application/json"})
        class NoRedirect(request.HTTPRedirectHandler):
            def redirect_request(self, req, fp, code, msg, headers, newurl):
                raise GatewayError("Redirect denied")
        opener = request.build_opener(request.ProxyHandler({}), NoRedirect())
        try:
            with opener.open(req, timeout=self.timeout) as response:
                payload = response.read(1_000_001)
            if len(payload) > 1_000_000:
                raise GatewayError("Response too large")
            data = json.loads(payload)
            if not isinstance(data, dict) or not isinstance(data.get("models"), list):
                raise GatewayError("Invalid model list")
            names = [x.get("name") for x in data["models"] if isinstance(x, dict)
                     and isinstance(x.get("name"), str)]
            return sorted(set(names))
        except (error.URLError, TimeoutError, OSError, UnicodeError,
                json.JSONDecodeError) as exc:
            raise GatewayError(f"Local Ollama failure: {type(exc).__name__}") from exc

    def chat(self, model, messages, max_tokens=256):
        """Text-only local Ollama /api/chat. No tool schemas are sent."""
        if not isinstance(model, str) or not 1 <= len(model) <= 100 or any(c in model for c in "\r\n\t /"):
            raise ValueError("Invalid model")
        if type(max_tokens) is not int or not 1 <= max_tokens <= 1024:
            raise ValueError("Invalid token limit")
        if not isinstance(messages, list) or not 2 <= len(messages) <= 26:
            raise ValueError("Need 2..26 chat messages")
        if not isinstance(messages[0], dict) or messages[0].get("role") != "system":
            raise ValueError("First message must be system context")
        length = 0
        allowed_roles = {"system", "user", "assistant"}
        for i, message in enumerate(messages):
            if not isinstance(message, dict) or set(message) != {"role", "content"}:
                raise ValueError("Messages must contain only role and content")
            role, content = message["role"], message["content"]
            if role not in allowed_roles or (i > 0 and role == "system"):
                raise ValueError("Invalid message role")
            if not isinstance(content, str) or not 1 <= len(content) <= 12000:
                raise ValueError("Invalid message length")
            length += len(content)
        if messages[-1]["role"] != "user" or length > 28000:
            raise ValueError("Chat must end with user message and fit context budget")
        body = json.dumps({"model": model, "messages": messages, "stream": False,
                           "options": {"num_predict": max_tokens}}, ensure_ascii=False).encode("utf-8")
        req = request.Request(self.endpoint + "/api/chat", data=body, method="POST",
                              headers={"Content-Type": "application/json"})
        class NoRedirect(request.HTTPRedirectHandler):
            def redirect_request(self, req, fp, code, msg, headers, newurl):
                raise GatewayError("Redirect denied")
        opener = request.build_opener(request.ProxyHandler({}), NoRedirect())
        try:
            with opener.open(req, timeout=self.timeout) as response:
                payload = response.read(2_000_001)
            if len(payload) > 2_000_000:
                raise GatewayError("Response too large")
            data = json.loads(payload.decode("utf-8"))
            response_message = data.get("message", {})
            answer = response_message.get("content") if isinstance(response_message, dict) else None
            if not isinstance(answer, str) or not answer.strip():
                raise GatewayError("Missing chat response")
            return answer
        except (error.URLError, TimeoutError, OSError, UnicodeError,
                json.JSONDecodeError) as exc:
            raise GatewayError(f"Local Ollama failure: {type(exc).__name__}") from exc
