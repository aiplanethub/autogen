import React from "react";
import { cn } from "../../../utils/utils";
import Icon from "../../../Icon";
import { IConversation } from "./Assistant";
// import MessageRenderer from "../chat/MessageRenderer.tsx";
// import { FileType } from "./AgentChat.tsx";
// import AgentChatUploads from "./AgentChatUploads.tsx";

const AgentChatMessage: React.FC<{ conversation: IConversation }> = ({
  conversation,
}) => {
  const isSender = conversation.role === "USER";

  return (
    <div
      className={cn("flex gap-2", isSender ? "flex-row-reverse" : "flex-row")}
    >
      {/* Icon - Only shown for AI */}
      {!isSender && (
        <div className="w-[36px] h-[36px] rounded-full bg-[#115E59] flex justify-center items-center my-2">
          <Icon name="brain" size={20} className="text-white" />
        </div>
      )}

      {/* Message Content */}
      <div
        className={cn(
          "flex flex-col items-start gap-y-4",
          isSender ? "items-end" : "items-start"
        )}
      >
        {!!conversation.content && (
          <div className={cn("p-3", isSender && "bg-secondary rounded-xl")}>
            {conversation.content}
          </div>
        )}
      </div>
    </div>
  );
};

export default AgentChatMessage;
