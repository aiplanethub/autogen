import React, { useEffect, useState } from "react";
import TaskRequirementInput from "./taskrequirementinput";
import AIWorkflowCreationSidebar from "./SideBar";
import {
  IAIWorkflowCreationKB,
  IAIWorkflowCreationSession,
} from "../../types/aiworkflowcreation";
import { message } from "antd";
import CreateSessionModal from "./CreateSessionModal";

const AIWorkflowCreationManager = () => {
  const [isSessionCreateModalOpen, setIsSessionCreateModalOpen] =
    useState(false);
  const [messageApi, contextHolder] = message.useMessage();
  const [isSidebarOpen, setIsSidebarOpen] = useState(() => {
    if (typeof window !== "undefined") {
      const stored = localStorage.getItem("sessionSidebar");
      return stored !== null ? JSON.parse(stored) : true;
    }
    return true; // Default value during SSR
  });

  // Persist sidebar state
  useEffect(() => {
    if (typeof window !== "undefined") {
      localStorage.setItem("sessionSidebar", JSON.stringify(isSidebarOpen));
    }
  }, [isSidebarOpen]);

  const [currentSession, setCurrentSession] =
    useState<IAIWorkflowCreationSession | null>(null);
  const [sessions, setSessions] = useState<Array<IAIWorkflowCreationSession>>(
    []
  );

  // Update URL when session changes
  useEffect(() => {
    if (currentSession?.id) {
      window.history.pushState(
        {},
        "",
        `?sessionId=${currentSession.id.toString()}`
      );
    }
  }, [currentSession?.id]);

  useEffect(() => {
    const fetchSession = () => {
      const data: Array<IAIWorkflowCreationSession> = [
        {
          id: 1,
          name: "User Proxy Session",
          knowledgebase: {
            id: "userproxysession",
            name: "UserProxySessionKB",
          },
        },
        {
          id: 2,
          name: "Assistant Agent Session",
          knowledgebase: {
            id: "assistantagentsession",
            name: "AssistantAgentSessionKB",
          },
        },
        {
          id: 3,
          name: "Web Agent Session",
          knowledgebase: {
            id: "webagentsession",
            name: "WebAgentSessionKB",
          },
        },
      ];
      setSessions(data);

      const params = new URLSearchParams(window.location.search);
      const sessionId = params.get("sessionId");

      if (data.length > 0) {
        if (sessionId === null && currentSession === null) {
          setCurrentSession(data[0]);
          window.history.pushState(
            {},
            "",
            `?sessionId=${data[0].id.toString()}`
          );
        }

        if (!!sessionId && currentSession === null) {
          const matchedSession = data.find(
            (session) => session.id === parseInt(sessionId)
          );
          if (!!matchedSession) {
            setCurrentSession(matchedSession);
            window.history.pushState(
              {},
              "",
              `?sessionId=${matchedSession.id.toString()}`
            );
          } else {
            message.error("Invalid sessionId");
            setCurrentSession(data[0]);
            window.history.pushState(
              {},
              "",
              `?sessionId=${data[0].id.toString()}`
            );
          }
        }
      }
    };
    fetchSession();
  }, []);

  const onSelectSession = (session: IAIWorkflowCreationSession) => {
    setCurrentSession(session);
  };

  const onCreateSession = () => {
    setIsSessionCreateModalOpen(true);
  };

  const onDeleteSession = (sessionId: number) => {
    const filteredSessions = sessions.filter(
      (session) => session.id !== sessionId
    );
    setSessions(filteredSessions);
    if (currentSession?.id === sessionId) {
      setCurrentSession(filteredSessions[0]);
      window.history.pushState(
        {},
        "",
        `?sessionId=${filteredSessions[0].id.toString()}`
      );
    }
    message.success("Session deleted successfully.");
  };

  const onSaveSession = (
    sessionName: string,
    knowledgeBase: IAIWorkflowCreationKB
  ) => {
    const session = {
      id: sessions.length + 1,
      name: sessionName,
      knowledgebase: knowledgeBase,
    };
    setSessions([...sessions, session]);
    setCurrentSession(session);
    window.history.pushState({}, "", `?sessionId=${session.id.toString()}`);
    message.success("Session created successfully.");
  };

  return (
    <div className="relative flex h-full w-full">
      {contextHolder}
      {/* Sidebar */}
      <div
        className={`absolute left-0 top-0 h-full transition-all duration-200 ease-in-out ${
          isSidebarOpen ? "w-64" : "w-12"
        }`}
      >
        <AIWorkflowCreationSidebar
          isOpen={isSidebarOpen}
          sessions={sessions}
          currentSession={currentSession}
          onToggle={() => setIsSidebarOpen(!isSidebarOpen)}
          onSelectSession={onSelectSession}
          onCreateSession={onCreateSession}
          onDeleteSession={onDeleteSession}
        />
      </div>

      {/* Main Content */}
      <div
        className={`flex-1 transition-all -mr-6 duration-200 ${
          isSidebarOpen ? "ml-64" : "ml-12"
        }`}
      >
        {sessions.length === 0 && currentSession === null ? (
          <div className="flex items-center justify-center h-[calc(100vh-120px)] text-secondary">
            Select a session from the sidebar or create a new one
          </div>
        ) : (
          <TaskRequirementInput />
        )}
      </div>

      {/* Create Session Modal */}
      {isSessionCreateModalOpen && (
        <CreateSessionModal
          isOpen={isSessionCreateModalOpen}
          onClose={() => setIsSessionCreateModalOpen(false)}
          onSaveSession={onSaveSession}
        />
      )}
    </div>
  );
};

export default AIWorkflowCreationManager;
