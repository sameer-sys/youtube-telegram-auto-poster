import http from "node:http";
import https from "node:https";

const PORT = parseInt(process.env.PORT || "8080", 10);

const server = http.createServer((req, res) => {
  const url = req.url || "";

  res.setHeader("Access-Control-Allow-Origin", "*");
  res.setHeader("Access-Control-Allow-Methods", "GET, POST, OPTIONS");
  res.setHeader("Access-Control-Allow-Headers", "*");

  if (req.method === "OPTIONS") {
    res.writeHead(204);
    res.end();
    return;
  }

  // Health check for Render / Railway / Koyeb
  if (url === "/" || url === "/health") {
    res.writeHead(200, { "Content-Type": "application/json" });
    res.end(JSON.stringify({ status: "ok", service: "omniroute-cloud", model: "boss" }));
    return;
  }

  // Models listing
  if (req.method === "GET" && (url.includes("/models") || url === "/v1/models")) {
    res.writeHead(200, { "Content-Type": "application/json" });
    res.end(JSON.stringify({
      object: "list",
      data: [{ id: "boss", object: "model", name: "Boss", owned_by: "omniroute", created: Date.now() }]
    }));
    return;
  }

  // Chat completions
  if (req.method === "POST" && url.includes("/chat/completions")) {
    let bodyRaw = "";
    req.on("data", chunk => bodyRaw += chunk);
    req.on("end", () => {
      try {
        const body = JSON.parse(bodyRaw);
        const isStream = Boolean(body.stream);
        delete body.tools;
        delete body.tool_choice;

        let cleanMessages = [];
        if (Array.isArray(body.messages)) {
          for (const m of body.messages) {
            if (!m) continue;
            let txt = typeof m.content === "string" ? m.content : (Array.isArray(m.content) ? m.content.map(c => c.text || "").join(" ") : String(m.content || ""));
            if (txt && txt.trim()) {
              const trimmed = txt.trim();
              cleanMessages.push({ role: m.role || "user", content: trimmed.length > 2000 ? trimmed.slice(-2000) : trimmed });
            }
          }
        }
        if (cleanMessages.length === 0) {
          cleanMessages.push({ role: "user", content: "Hello" });
        }
        if (cleanMessages.length > 10) {
          const system = cleanMessages.filter(m => m.role === "system");
          const rest = cleanMessages.filter(m => m.role !== "system");
          cleanMessages = [...system, ...rest.slice(-8)];
        }

        const lastUserMsg = cleanMessages[cleanMessages.length - 1]?.content || "Hello";
        const upstreamPayload = JSON.stringify({
          model: "openai-fast",
          messages: cleanMessages,
          stream: false
        });

        const sendDone = (replyText) => {
          if (res.headersSent) return;
          const text = (replyText && replyText.trim()) ? replyText.trim() : "I am here. How can I help you?";
          if (isStream) {
            res.writeHead(200, {
              "Content-Type": "text/event-stream",
              "Cache-Control": "no-cache",
              "Connection": "keep-alive"
            });
            const c1 = JSON.stringify({
              id: "chatcmpl-boss-" + Date.now(),
              object: "chat.completion.chunk",
              created: Math.floor(Date.now() / 1000),
              model: "boss",
              choices: [{ index: 0, delta: { role: "assistant", content: text }, finish_reason: null }]
            });
            const c2 = JSON.stringify({
              id: "chatcmpl-boss-" + Date.now(),
              object: "chat.completion.chunk",
              created: Math.floor(Date.now() / 1000),
              model: "boss",
              choices: [{ index: 0, delta: {}, finish_reason: "stop" }]
            });
            res.write(`data: ${c1}\n\n`);
            res.write(`data: ${c2}\n\n`);
            res.write("data: [DONE]\n\n");
            res.end();
          } else {
            res.writeHead(200, { "Content-Type": "application/json" });
            res.end(JSON.stringify({
              id: "chatcmpl-boss-" + Date.now(),
              object: "chat.completion",
              created: Math.floor(Date.now() / 1000),
              model: "boss",
              choices: [{
                index: 0,
                message: { role: "assistant", content: text },
                finish_reason: "stop"
              }],
              usage: { prompt_tokens: 10, completion_tokens: 10, total_tokens: 20 }
            }));
          }
        };

        const fallbackGet = () => {
          const safeText = encodeURIComponent((lastUserMsg || "Hello").slice(0, 300));
          https.get(`https://text.pollinations.ai/${safeText}`, (fRes) => {
            let fRaw = "";
            fRes.on("data", c => fRaw += c);
            fRes.on("end", () => {
              if (fRaw && fRaw.trim() && !fRaw.includes("Request-URI Too Large")) {
                sendDone(fRaw.trim());
              } else {
                sendDone("I am here and ready to assist you.");
              }
            });
          }).on("error", () => {
            sendDone("I am ready to help.");
          });
        };

        const upstreamReq = https.request({
          hostname: "text.pollinations.ai",
          path: "/openai/chat/completions",
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "Content-Length": Buffer.byteLength(upstreamPayload),
            "Connection": "close"
          },
          timeout: 25000
        }, (upstreamRes) => {
          if (upstreamRes.statusCode !== 200) {
            fallbackGet();
            return;
          }
          let resRaw = "";
          upstreamRes.on("data", c => resRaw += c);
          upstreamRes.on("end", () => {
            try {
              const parsed = JSON.parse(resRaw);
              const out = parsed?.choices?.[0]?.message?.content || parsed?.choices?.[0]?.message?.reasoning;
              if (out && out.trim()) {
                sendDone(out.trim());
              } else {
                fallbackGet();
              }
            } catch {
              fallbackGet();
            }
          });
        });

        upstreamReq.on("error", () => fallbackGet());
        upstreamReq.on("timeout", () => {
          upstreamReq.destroy();
          fallbackGet();
        });

        upstreamReq.write(upstreamPayload);
        upstreamReq.end();
      } catch {
        sendDone("Hello! How can I help you today?");
      }
    });
    return;
  }

  res.writeHead(404, { "Content-Type": "application/json" });
  res.end(JSON.stringify({ error: { message: "Not found", code: 404 } }));
});

server.listen(PORT, "0.0.0.0", () => {
  console.log(`[OmniRoute Cloud] Listening on 0.0.0.0:${PORT}`);
});
