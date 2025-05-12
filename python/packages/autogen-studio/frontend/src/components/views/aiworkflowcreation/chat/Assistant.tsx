import React, { useState } from "react";
import Conversations from "./Conversations";
import TaskRequirementInput from "./TaskRequirementInput";

type RoleType = "AI" | "USER";

export interface IConversation {
  role: RoleType;
  content: string;
}

const Assistant = () => {
  const [conversations, setConversations] = useState<Array<IConversation>>([
    { role: "USER", content: "create a agent" },
    { role: "AI", content: "sure" },
    { role: "USER", content: "create a agent" },
    { role: "AI", content: "sure" },
    { role: "USER", content: "create a agent" },
    { role: "AI", content: "sure" },
    { role: "USER", content: "create a agent" },
    { role: "AI", content: "sure" },
    { role: "USER", content: "create a agent" },
    { role: "AI", content: "sure" },
    { role: "USER", content: "create a agent" },
    { role: "AI", content: "sure" },
    { role: "USER", content: "create a agent" },
    { role: "AI", content: "sure" },
    { role: "USER", content: "create a agent" },
    { role: "AI", content: "sure" },
    { role: "USER", content: "create a agent" },
    { role: "AI", content: "sure" },
    { role: "AI", content: "sure" },
    { role: "USER", content: "create a agent" },
    { role: "AI", content: "sure" },
    { role: "USER", content: "create a agent" },
    { role: "AI", content: "sure" },
    { role: "USER", content: "create a agent" },
    { role: "AI", content: "sure" },
  ]);

  return (
    <div className="flex flex-col justify-center items-center w-full h-full max-h-[calc(100vh_-_158px)]">
      {conversations.length > 0 && (
        <Conversations conversations={conversations} />
      )}
      <TaskRequirementInput hasConversations={conversations?.length > 0} />
    </div>
  );
};

export default Assistant;
