import React, { useState } from "react";
import Conversations from "./Conversations";
import TaskRequirementInput from "./TaskRequirementInput";

type RoleType = "AI" | "USER";

export interface IConversation {
  id: string;
  role: RoleType;
  content: string;
}

type Props = {
  builder_id: number
  gallery_id?: number
  // knowledge_base: string
}

const Assistant = (props: Props) => {
  const [conversations, setConversations] = useState<Array<IConversation>>([]);


  return (
    <div className="flex flex-col justify-center items-center w-full h-full max-h-[calc(100vh_-_158px)]">
      {conversations.length > 0 && (
        <Conversations conversations={conversations} />
      )}
      <TaskRequirementInput setConversations={setConversations} builder_id={props.builder_id} hasConversations={conversations.length > 0} />
    </div>
  );
};

export default Assistant;
