const BACKEND_URL = "http://127.0.0.1:8000";

// pc → RTCPeerConnection (WebRTC connection)
// dc → Data channel (control + events)
// ms → MediaStream (your microphone audio)

let pc, dc, ms;

const startBtn = document.getElementById("startBtn");
const stopBtn = document.getElementById("stopBtn");
const logEl = document.getElementById("log");

function print(...args) {
  console.log(...args);
  logEl.textContent += args
    .map((a) => (typeof a === "string" ? a : JSON.stringify(a)))
    .join(" ") + "\n";
  logEl.scrollTop = logEl.scrollHeight;
}

startBtn.onclick = startCall;
stopBtn.onclick = stopCall;

async function startCall() {
  startBtn.disabled = true;
  print("requesting ephemeral token from our backend...");

  // 1. Get a short-lived token from OUR backend.
  //    The real API key never touches the browser.
  const tokenResp = await fetch(`${BACKEND_URL}/token`);
  const tokenData = await tokenResp.json();
  const EPHEMERAL_KEY = tokenData.value;

  // 2. Create the WebRTC peer connection.
  pc = new RTCPeerConnection();

  // 3. Play the model's voice through a hidden <audio> element.
  const audioEl = document.createElement("audio");
  audioEl.autoplay = true;
  document.body.appendChild(audioEl);
  pc.ontrack = (e) => {
    audioEl.srcObject = e.streams[0];
  };

  // 4. Capture the mic and add it to the peer connection.
  ms = await navigator.mediaDevices.getUserMedia({ audio: true });
  ms.getTracks().forEach((track) => pc.addTrack(track, ms));

  // 5. Data channel: this carries session events, transcripts, and
  //    tool-call requests/results. This is the "signaling" you were
  //    picturing, but it runs OVER the WebRTC connection itself --
  //    there's no separate signaling server needed for this part.
  dc = pc.createDataChannel("oai-events");
  dc.addEventListener("open", () => print("data channel open"));
  dc.addEventListener("message", handleServerEvent);

  // 6. SDP offer/answer handshake, straight from browser to OpenAI,
  //    authenticated with the ephemeral key (not your real API key).
  const offer = await pc.createOffer();
  await pc.setLocalDescription(offer);

  const sdpResponse = await fetch("https://api.openai.com/v1/realtime/calls", {
    method: "POST",
    body: offer.sdp,
    headers: {
      Authorization: `Bearer ${EPHEMERAL_KEY}`,
      "Content-Type": "application/sdp",
    },
  });

  const answer = { type: "answer", sdp: await sdpResponse.text() };
  await pc.setRemoteDescription(answer);

  stopBtn.disabled = false;
  print("call started -- talk into your mic");
}

function stopCall() {
  if (dc) dc.close();
  if (pc) pc.close();
  if (ms) ms.getTracks().forEach((t) => t.stop());
  startBtn.disabled = false;
  stopBtn.disabled = true;
  print("call stopped");
}

async function handleServerEvent(e) {
  const event = JSON.parse(e.data);

  switch (event.type) {
    case "response.output_audio_transcript.delta":
      // Live transcript of what the model is saying, piece by piece.
      logEl.textContent += event.delta;
      break;

    case "response.output_item.done":
      // A completed item -- check if it was a tool call.
      if (event.item?.type === "function_call") {
        await handleFunctionCall(event.item);
      }
      break;

    case "error":
      print("server error:", event.error);
      break;

    default:
      // Uncomment while learning, to see the full event stream:
      // print(event.type);
      break;
  }
}

async function handleFunctionCall(item) {
  print("tool call requested:", item.name, item.arguments);

  // Forward to OUR backend instead of running anything in the browser.
  // This is where permissions/logging/budgets actually get enforced.
  const resp = await fetch(`${BACKEND_URL}/tools/execute`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      name: item.name,
      arguments: JSON.parse(item.arguments || "{}"),
    }),
  });
  const { result } = await resp.json();

  // Send the tool's result back to the model over the data channel.
  dc.send(
    JSON.stringify({
      type: "conversation.item.create",
      item: {
        type: "function_call_output",
        call_id: item.call_id,
        output: JSON.stringify(result),
      },
    })
  );

  // Ask the model to continue now that it has the tool result.
  dc.send(JSON.stringify({ type: "response.create" }));
}
