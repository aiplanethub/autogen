import React, { useEffect, useState } from "react";
import Conversations from "./Conversations";
import TaskRequirementInput from "./TaskRequirementInput";
import { chatAPI } from "./api"

type RoleType = "AI" | "USER";

export interface IConversation {
  role: RoleType;
  content: string;
}

type Props = {
  builder_id: number
  gallery_id: number
  // knowledge_base: string
}

const Assistant = (props: Props) => {
  const [conversations, setConversations] = useState<Array<IConversation>>([]);
  const [controller, setController] = useState<AbortController | null>(null)
  const [taskRequirement, setTaskRequirement] = useState("");


  const on_message = (data: { id: string; data: any }) => {
    setConversations((prev) => [...prev, { id: data.id, role: data.data.role, content: data.data.text }]);
  }

  const build_agent_callback = async () => {
    // stop the previous request and start a new one
    if (controller) {
      controller.abort()
      setController(new AbortController())
    }

    if (!controller) {
      setController(new AbortController())
    }

    await chatAPI.streamConversations({
      builder_id: props.builder_id,
      gallery_id: props.gallery_id,
      prompt: taskRequirement,
      // knowledge_base: knowledge_base
    }, controller!, on_message)
  }

  return (
    <div className="flex flex-col justify-center items-center w-full h-full max-h-[calc(100vh_-_158px)]">
      {conversations.length > 0 && (
        <Conversations conversations={conversations} />
      )}
      <TaskRequirementInput build_agent_callback={build_agent_callback} builder_id={props.builder_id} taskRequirement={taskRequirement} setTaskRequirement={setTaskRequirement} hasConversations={conversations?.length > 0} />
    </div>
  );
};

export default Assistant;
