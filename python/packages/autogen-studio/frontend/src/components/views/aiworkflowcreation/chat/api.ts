import { BaseAPI } from "../../../utils/baseapi";

import {
    fetchEventSource,
    EventStreamContentType,
} from "@microsoft/fetch-event-source";

class FatalError extends Error { }
export class ChatAPI extends BaseAPI {
    async streamConversations(
        data: {
            builder_id: number;
            gallery_id: number;
            prompt: string;
            // knowledge_base?: string; // not implemented in ui
        },
        controller: AbortController,
        on_message: (data: any) => void
    ) {
        console.log("data", data)
        const formData = new FormData();
        formData.append("builder_id", data.builder_id.toString());
        formData.append("gallery_id", data.gallery_id.toString());
        formData.append("prompt", data.prompt);

        // if (data.knowledge_base)
        //     formData.append("knowledge_base", data.knowledge_base);

        await fetchEventSource(`${this.getBaseUrl()}/teams/plan`, {
            method: "POST",
            headers: {},
            body: formData,
            signal: controller.signal,
            credentials: "include",
            async onopen(response) {
                console.log("onopen", response);
                if (
                    response.ok &&
                    response.headers.get("content-type") === EventStreamContentType
                ) {
                    console.log("everything is good");
                    return; // everything's good
                } else if (
                    response.status >= 400 &&
                    response.status < 500 &&
                    response.status !== 429
                ) {
                    // client-side errors are usually non-retriable:
                    throw new FatalError();
                } else {
                    // NOTE: This triggers for POST, but not GET. Not sure why
                    console.log("retriableerror");
                    // throw new RetriableError();
                }
            },

            onmessage(event) {
                // if the server emits an error message, throw an exception
                // so it gets handled by the onerror callback below:
                if (event.event === "FatalError") {
                    throw new FatalError(event.data);
                }
                console.log(event);
                on_message({ id: event.id, data: event.data }); // for react code
            },
            onclose() {
                // if the server closes the connection unexpectedly, retry:
                console.log("onclose");
                // throw new RetriableError();
            },
            onerror(err) {
                controller.abort()
                if (err instanceof FatalError) {
                    throw err; // rethrow to stop the operation
                } else {
                    console.log("onerror");
                    // do nothing to automatically retry. You can also
                    // return a specific retry interval here.
                }
            },
        });
    }

    getWebsocketURL() {
        let url = this.getBaseUrl()
        if (url.startsWith("http")) {
            url = url.replace("http", "ws")
        } else if (url.startsWith("https")) {
            url = url.replace("https", "wss")
        }

        url = `${url}/teams/ws/builder_id`

        return url
    }

    setupWebsocketConnection(builder_id: number) {
        const ws_url = this.getWebsocketURL().replace("builder_id", builder_id.toString())
        const socket = new WebSocket(ws_url)
        return socket
    }
}

export const chatAPI = new ChatAPI();
