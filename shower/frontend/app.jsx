// // import RecorderNode from "./recorder-node.js";

// // const { useState, useEffect, useCallback, useRef } = React;

// // const { createMachine, assign } = XState;
// // const { useMachine } = XStateReact;

// // const SILENT_DELAY = 4000; // in milliseconds
// // const CANCEL_OLD_AUDIO = false; // TODO: set this to true after cancellations don't terminate containers.
// // const INITIAL_MESSAGE = "Hi! I'm a language model running on Modal. I will now scrape your emails and generate a summary.";

// // const INDICATOR_TYPE = {
// //   TALKING: "talking",
// //   SILENT: "silent",
// //   GENERATING: "generating",
// //   IDLE: "idle",
// // };

// // const chatMachine = createMachine(
// //   {
// //     initial: "botGenerating",
// //     context: {
// //       pendingSegments: 0,
// //       transcript: "",
// //       messages: 1,
// //     },
// //     states: {
// //       botGenerating: {
// //         on: {
// //           GENERATION_DONE: { target: "botDone", actions: "resetTranscript" },
// //         },
// //       },
// //       botDone: {
// //         on: {
// //           TYPING_DONE: {
// //             target: "botDone",
// //             actions: ["resetPendingSegments", "incrementMessages"],
// //           },
// //         },
// //       },
// //     },
// //   },
// //   {
// //     actions: {
// //       resetPendingSegments: assign({ pendingSegments: 0 }),
// //       incrementMessages: assign({
// //         messages: (context) => context.messages + 1,
// //       }),
// //       resetTranscript: assign({ transcript: "" }),
// //     },
// //   }
// // );

// // function LoadingSpinner() {
// //   return (
// //     <div className="scale-[0.2] w-6 h-6 flex items-center justify-center">
// //       <div className="lds-spinner [&>div:after]:bg-zinc-200">
// //         {[...Array(12)].map((_, i) => (
// //           <div key={i}></div>
// //         ))}
// //       </div>
// //     </div>
// //   );
// // }

// // function ChatMessage({ text, isUser, indicator }) {
// //   return (
// //     <div className="w-full">
// //       <div className="text-base gap-4 p-4 flex m-auto">
// //         <div className="flex flex-col gap-2">
// //           {indicator == INDICATOR_TYPE.GENERATING && <LoadingSpinner />}
// //         </div>
// //         <div>
// //           <div
// //             className={
// //               "whitespace-pre-wrap rounded-[16px] px-3 py-1.5 max-w-[600px] bg-zinc-800 border " +
// //               (!text
// //                 ? " pulse text-sm text-zinc-300 border-gray-600"
// //                 : isUser
// //                 ? " text-zinc-100 border-yellow-500"
// //                 : " text-zinc-100 border-primary")
// //             }
// //           >
// //             {text || (isUser ? "" : "Bot is typing...")}
// //           </div>
// //         </div>
// //       </div>
// //     </div>
// //   );
// // }

// // class PlayQueue {
// //   constructor(audioContext, onChange) {
// //     this.call_ids = [];
// //     this.audioContext = audioContext;
// //     this._onChange = onChange;
// //     this._isProcessing = false;
// //     this._indicators = {};
// //   }

// //   async add(item) {
// //     this.call_ids.push(item);
// //     this.play();
// //   }

// //   _updateState(idx, indicator) {
// //     this._indicators[idx] = indicator;
// //     this._onChange(this._indicators);
// //   }

// //   _onEnd(idx) {
// //     this._updateState(idx, INDICATOR_TYPE.IDLE);
// //     this._isProcessing = false;
// //     this.play();
// //   }

// //   async play() {
// //     if (this._isProcessing || this.call_ids.length === 0) {
// //       return;
// //     }

// //     this._isProcessing = true;

// //     const [payload, idx] = this.call_ids.shift();
// //     this._updateState(idx, INDICATOR_TYPE.GENERATING);

// //     const call_id = payload;
// //     console.log("Fetching audio for call", call_id, idx);

// //     let response;
// //     let success = false;
// //     while (true) {
// //       response = await fetch(`/audio/${call_id}`);
// //       if (response.status === 202) {
// //         continue;
// //       } else if (response.status === 204) {
// //         console.error("No audio found for call: " + call_id);
// //         break;
// //       } else if (!response.ok) {
// //         console.error("Error occurred fetching audio: " + response.status);
// //       } else {
// //         success = true;
// //         break;
// //       }
// //     }

// //     if (!success) {
// //       this._onEnd(idx);
// //       return;
// //     }

// //     const arrayBuffer = await response.arrayBuffer();
// //     const audioBuffer = await this.audioContext.decodeAudioData(arrayBuffer);

// //     const source = this.audioContext.createBufferSource();
// //     source.buffer = audioBuffer;
// //     source.connect(this.audioContext.destination);

// //     source.onended = () => this._onEnd(idx);

// //     this._updateState(idx, INDICATOR_TYPE.TALKING);
// //     source.start();
// //   }

// //   clear() {
// //     for (const [call_id, _] of this.call_ids) {
// //       fetch(`/audio/${call_id}`, { method: "DELETE" });
// //     }
// //     this.call_ids = [];
// //   }
// // }

// // async function fetchScrape() {
// //   const response = await fetch("/scraper", {
// //     method: "POST",
// //     headers: { "Content-Type": "application/json" },
// //   });

// //   if (!response.ok) {
// //     console.error("Error occurred during email scraping: " + response.status);
// //   }

// //   return await response.json();
// // }

// // async function* fetchGeneration(prompt) {
// //   const body = { prompt, tts: true };

// //   const response = await fetch("/generate", {
// //     method: "POST",
// //     body: JSON.stringify(body),
// //     headers: { "Content-Type": "application/json" },
// //   });

// //   if (!response.ok) {
// //     console.error("Error occurred during generation: " + response.status);
// //   }

// //   const readableStream = response.body;
// //   const decoder = new TextDecoder();

// //   const reader = readableStream.getReader();

// //   while (true) {
// //     const { done, value } = await reader.read();

// //     if (done) {
// //       break;
// //     }

// //     for (let message of decoder.decode(value).split("\x1e")) {
// //       if (message.length === 0) {
// //         continue;
// //       }

// //       const { type, value: payload } = JSON.parse(message);

// //       yield { type, payload };
// //     }
// //   }

// //   reader.releaseLock();
// // }

// // function App() {
// //   const [history, setHistory] = useState([]);
// //   const [fullMessage, setFullMessage] = useState(INITIAL_MESSAGE);
// //   const [typedMessage, setTypedMessage] = useState("");
// //   const [botIndicators, setBotIndicators] = useState({});
// //   const [state, send, service] = useMachine(chatMachine);
// //   const playQueueRef = useRef(null);

// //   useEffect(() => {
// //     const subscription = service.subscribe((state, event) => {
// //       console.log("Transitioned to state:", state.value, state.context);
// //     });

// //     return subscription.unsubscribe;
// //   }, [service]);

// //   const generateResponse = useCallback(async () => {
// //     console.log("Generating response", history);

// //     const { prompt } = await fetchScrape();

// //     console.log("Prompt:", prompt)

// //     let firstAudioRecvd = false;
// //     for await (let { type, payload } of fetchGeneration(prompt)) {
// //       if (type === "text") {
// //         setFullMessage((m) => m + payload);
// //       } else if (type === "audio") {
// //         if (!firstAudioRecvd && CANCEL_OLD_AUDIO) {
// //           playQueueRef.current.clear();
// //           firstAudioRecvd = true;
// //         }
// //         playQueueRef.current.add([payload, history.length + 1]);
// //       }
// //     }

// //     console.log("Finished generating response");

// //     send("GENERATION_DONE");
// //   }, [history]);

// //   useEffect(() => {
// //     const transition = state.context.messages > history.length + 1;

// //     if (transition && state.matches("botGenerating")) {
// //       generateResponse();
// //     }

// //     if (transition) {
// //       setHistory((h) => [...h, fullMessage]);
// //       setFullMessage("");
// //       setTypedMessage("");
// //     }
// //   }, [state, history, fullMessage]);

// //   const tick = useCallback(() => {
// //     if (typedMessage.length < fullMessage.length) {
// //       const n = 1;
// //       setTypedMessage(fullMessage.substring(0, typedMessage.length + n));

// //       if (typedMessage.length + n == fullMessage.length) {
// //         send("TYPING_DONE");
// //       }
// //     }
// //   }, [typedMessage, fullMessage]);

// //   useEffect(() => {
// //     const intervalId = setInterval(tick, 20);
// //     return () => clearInterval(intervalId);
// //   }, [tick]);

// //   async function onMount() {
// //     const context = new AudioContext();
// //     playQueueRef.current = new PlayQueue(context, setBotIndicators);
// //   }

// //   useEffect(() => {
// //     onMount();
// //   }, []);

// //   const isUserLast = history.length % 2 == 1;

// //   useEffect(() => {
// //     console.log("Bot indicator changed", botIndicators);
// //   }, [botIndicators]);

// //   console.log(history)

// //   return (
// //     <div className="min-w-full min-h-screen screen">
// //       <div className="w-full h-screen flex">
// //         <main className="bg-zinc-800 w-full flex flex-col items-center gap-3 pt-6 overflow-auto">
// //           {history.map((msg, i) => (
// //             <ChatMessage
// //               key={i}
// //               text={msg}
// //               isUser={i % 2 == 1}
// //               indicator={i % 2 == 0 && botIndicators[i]}
// //             />
// //           ))}
// //           {/* <ChatMessage
// //             text={typedMessage}
// //             isUser={isUserLast}
// //             indicator={isUserLast ? INDICATOR_TYPE.IDLE : botIndicators[history.length]}
// //           /> */}
// //         </main>
// //       </div>
// //     </div>
// //   );
// // }

// // const container = document.getElementById("react");
// // ReactDOM.createRoot(container).render(<App />);


// import React, { useEffect, useState } from 'react';

// async function fetchScrape() {
//   const response = await fetch('/scraper', {
//     method: 'POST',
//     headers: { 'Content-Type': 'application/json' },
//   });

//   if (!response.ok) {
//     console.error('Error occurred during email scraping: ' + response.status);
//     return null;
//   }

//   return await response.json();
// }

// function App() {
//   const [isLoading, setIsLoading] = useState(true);
//   const [error, setError] = useState(null);
//   const [data, setData] = useState(null);

//   useEffect(() => {
//     const fetchData = async () => {
//       try {
//         console.log('Fetching data...')
//         const result = await fetchScrape();
//         setData(result);
//         console.log('Scraped data:', result);
//       } catch (error) {
//         setError(error);
//         console.error('Error occurred during email scraping:', error);
//       } finally {
//         setIsLoading(false);
//       }
//     };

//     fetchData();
//   }, []);

//   if (isLoading) {
//     return <div>Loading...</div>;
//   }

//   if (error) {
//     return <div>Error: {error.message}</div>;
//   }

//   return (
//     <div>
//       <h1>Email Scraper</h1>
//       {data ? (
//         <div>
//           <p>Scraping completed successfully.</p>
//           <pre>{JSON.stringify(data, null, 2)}</pre>
//         </div>
//       ) : (
//         <p>No data available.</p>
//       )}
//     </div>
//   );
// }

// export default App;


import React, { useEffect, useState } from 'react';

async function fetchScrape() {
  const response = await fetch('/scraper', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
  });

  if (!response.ok) {
    throw new Error('Error occurred during email scraping: ' + response.status);
  }

  return await response.text();
}

function App() {
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  const [data, setData] = useState(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const result = await fetchScrape();
        setData(result);
        console.log('Scraped data:', result);
      } catch (error) {
        setError(error.message);
        console.error('Error occurred during email scraping:', error);
      } finally {
        setIsLoading(false);
      }
    };

    fetchData();
  }, []);

  if (isLoading) {
    return <div>Loading...</div>;
  }

  if (error) {
    return <div>Error: {error}</div>;
  }

  return (
    <div>
      <h1>Email Scraper</h1>
      {data ? (
        <div>
          <p>Scraping completed successfully.</p>
          <pre>{data}</pre>
        </div>
      ) : (
        <p>No data available.</p>
      )}
    </div>
  );
}

export default App;