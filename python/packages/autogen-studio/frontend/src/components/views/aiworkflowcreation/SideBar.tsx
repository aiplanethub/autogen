import React, { useState } from "react";
import { Button, Tooltip } from "antd";
import {
  Plus,
  Trash2,
  PanelLeftClose,
  PanelLeftOpen,
  RefreshCw,
  Info,
} from "lucide-react";
import { IAIWorkflowCreationSidebarProps } from "../../types/aiworkflowcreation";

export const AIWorkflowCreationSidebar: React.FC<
  IAIWorkflowCreationSidebarProps
> = ({
  isOpen,
  sessions,
  currentSession,
  onToggle,
  onSelectSession,
  onCreateSession,
  onDeleteSession,
  isLoading = false,
}) => {
  // Render collapsed state
  if (!isOpen) {
    return (
      <div className="h-full border-r border-secondary">
        <div className="p-2 -ml-2">
          <Tooltip title={`Sessions (${sessions.length})`}>
            <button
              onClick={onToggle}
              className="p-2 rounded-md hover:bg-secondary hover:text-accent text-secondary transition-colors focus:outline-none focus:ring-2 focus:ring-accent focus:ring-opacity-50"
            >
              <PanelLeftOpen strokeWidth={1.5} className="h-6 w-6" />
            </button>
          </Tooltip>
        </div>

        <div className="mt-4 px-2 -ml-1">
          <Tooltip title="Create new session">
            <Button
              type="text"
              className="w-full p-2 flex justify-center"
              onClick={onCreateSession}
              icon={<Plus className="w-4 h-4" />}
            />
          </Tooltip>
        </div>
      </div>
    );
  }

  // Render expanded state
  return (
    <div className="h-full border-r border-secondary">
      {/* Header */}
      <div className="flex items-center justify-between pt-0 p-4 pl-2 pr-2 border-b border-secondary">
        <div className="flex items-center gap-2">
          <span className="text-primary font-medium">Sessions</span>
          <span className="px-2 py-0.5 text-xs bg-accent/10 text-accent rounded">
            {sessions.length}
          </span>
        </div>
        <Tooltip title="Close Sidebar">
          <button
            onClick={onToggle}
            className="p-2 rounded-md hover:bg-secondary hover:text-accent text-secondary transition-colors focus:outline-none focus:ring-2 focus:ring-accent focus:ring-opacity-50"
          >
            <PanelLeftClose strokeWidth={1.5} className="h-6 w-6" />
          </button>
        </Tooltip>
      </div>

      {/* Create Session Button */}
      <div className="my-4 flex text-sm">
        <div className="mr-2 w-full">
          <Tooltip title="Create new session">
            <Button
              type="primary"
              className="w-full"
              icon={<Plus className="w-4 h-4" />}
              onClick={onCreateSession}
            >
              New Session
            </Button>
          </Tooltip>
        </div>
      </div>

      {/* Section Label */}
      <div className="py-2 flex text-sm text-secondary">
        <div className="flex">All Sessions</div>
        {isLoading && <RefreshCw className="w-4 h-4 ml-2 animate-spin" />}
      </div>

      {/* Sessions List */}
      {!isLoading && sessions.length === 0 && (
        <div className="p-2 mr-2 text-center text-secondary text-sm border border-dashed rounded">
          <Info className="w-4 h-4 inline-block mr-1.5 -mt-0.5" />
          No sesions found
        </div>
      )}

      <div className="scroll overflow-y-auto h-[calc(100%-170px)]">
        {sessions.map((session) => (
          <div key={session.id} className="relative border-secondary">
            <div
              className={`absolute top-1 left-0.5 z-50 h-[calc(100%-8px)] w-1 bg-opacity-80 rounded ${
                currentSession?.id === session.id ? "bg-accent" : "bg-tertiary"
              }`}
            />
            {session && (
              <div
                className={`group ml-1 flex flex-col p-3 rounded-l cursor-pointer hover:bg-secondary ${
                  currentSession?.id === session.id
                    ? "border-accent bg-secondary"
                    : "border-transparent"
                }`}
                onClick={() => onSelectSession(session)}
              >
                {/* Gallery Name and Actions Row */}
                <div className="flex items-center justify-between min-w-0">
                  <div className="flex items-center gap-2 min-w-0 flex-1">
                    <div className="truncate flex-1">
                      <span className="font-medium">{session.name}</span>
                    </div>
                  </div>
                  <div className="flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity ml-2 flex-shrink-0">
                    <Tooltip
                      title={
                        sessions.length === 1
                          ? "Cannot delete the last session"
                          : "Delete session"
                      }
                    >
                      <Button
                        type="text"
                        size="small"
                        className="p-0 min-w-[24px] h-6"
                        danger
                        disabled={sessions.length === 1}
                        icon={<Trash2 className="w-4 h-4 text-red-500" />}
                        onClick={(e) => {
                          e.stopPropagation();
                          onDeleteSession(session.id!);
                        }}
                      />
                    </Tooltip>
                  </div>
                </div>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
};

export default AIWorkflowCreationSidebar;
