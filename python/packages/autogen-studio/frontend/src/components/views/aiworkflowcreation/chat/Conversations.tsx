import React, { useEffect, useRef } from "react";
import { IConversation } from "./Assistant";
import Message from "./Message";

const Conversations: React.FC<{ conversations: Array<IConversation> }> = ({
  conversations,
}) => {
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    // Auto-scroll to bottom when messages change
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [conversations]);

  return (
    <div className="flex w-full h-full items-end px-4 py-2 max-h-[calc(100vh_-_290px)]">
      <div className="flex flex-col space-y-4 w-full h-full overflow-y-auto">
        <div ref={messagesEndRef}>
          {conversations.map((conversation, idx) => (
            <Message conversation={conversation} />
          ))}
        </div>
      </div>
    </div>
  );
};

export default Conversations;
