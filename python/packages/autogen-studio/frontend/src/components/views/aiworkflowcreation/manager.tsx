import React, { useContext, useEffect, useState } from "react";
import Assistant from "./chat/Assistant";
import AIWorkflowCreationSidebar from "./SideBar";
import { IAIWorkflowCreationSession } from "../../types/aiworkflowcreation";
import { message } from "antd";
import CreateSessionModal from "./CreateSessionModal";
import Icon from "../../Icon";
import { aiWorkflowCreationAPI } from "./api";
import { appContext } from "../../../hooks/provider";

const AIWorkflowCreationManager = () => {
  const { user } = useContext(appContext);
  const [isLoading, setIsLoading] = useState(false);
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
    const fetchSession = async () => {
      if (!user?.id) return;
      try {
        setIsLoading(true);
        const data = await aiWorkflowCreationAPI.listAIWorkflowCreationSessions(
          user?.id
        );

        if (data.length > 0) {
          const params = new URLSearchParams(window.location.search);
          const sessionId = params.get("sessionId");
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
              (session) => session.id === sessionId
            );
            if (!!matchedSession) {
              setCurrentSession(matchedSession);
              window.history.pushState(
                {},
                "",
                `?sessionId=${matchedSession.id}`
              );
            } else {
              message.error("Invalid sessionId");
              setCurrentSession(data[0]);
              window.history.pushState({}, "", `?sessionId=${data[0].id}`);
            }
          }
        }
        setSessions(data);
      } catch (error) {
        console.error("Error fetching ai workflow creation sessions:", error);
        messageApi.error("Failed to fetch ai workflow creation sessions");
      } finally {
        setIsLoading(false);
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

  const onDeleteSession = (sessionId: string) => {
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

  const onSaveSession = async (sessionName: string) => {
    if (!user?.id) return;
    try {
      const session =
        await aiWorkflowCreationAPI.createAIWorkflowCreationSession(
          { name: sessionName },
          user.id
        );
      setSessions([session, ...sessions]);
      setCurrentSession(session);
      window.history.pushState({}, "", `?sessionId=${session.id}`);
      message.success("Session created successfully.");
    } catch (error) {
      console.error("Error creating ai workflow creation sessions:", error);
      messageApi.error("Failed to create ai workflow creation session");
    }
  };

  return (
    <div className="relative flex h-full w-full">
      {contextHolder}
      {isLoading ? (
        <div className="h-full w-full flex justify-center items-center">
          Loading
        </div>
      ) : (
        <>
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
            <div className="px-4 py-2 w-full h-full">
              {/* Breadcrumb */}
              <div className="flex items-center gap-2 text-sm">
                <span className="text-primary font-medium">Sessions</span>
                {currentSession && (
                  <>
                    <Icon
                      name="chevronright"
                      className="w-4 h-4 text-secondary"
                    />
                    <span className="text-secondary">
                      {currentSession.name}
                    </span>
                  </>
                )}
              </div>

              {/* Content Area */}
              {sessions.length === 0 && currentSession === null ? (
                <div className="flex items-center justify-center h-[calc(100vh-120px)] text-secondary">
                  Select a session from the sidebar or create a new one
                </div>
              ) : (
                <Assistant />
              )}
            </div>
          </div>
        </>
      )}

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
