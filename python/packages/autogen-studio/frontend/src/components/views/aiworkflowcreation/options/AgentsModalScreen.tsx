import React, { useMemo, useState } from "react";
import Icon from "../../../Icon";
import useDebounce from "../../../utils/utils";
import ListItem from "./ListItem";
import { AgentAndToolProps } from "../../../types/aiworkflowcreation";

const AgentsModalScreen: React.FC<{
  selectedGallery: string;
  onChangeGallery: () => void;
  agents: AgentAndToolProps[];
  onToggleAgent: (id: string) => void;
}> = ({ selectedGallery, onChangeGallery, agents, onToggleAgent }) => {
  const [searchTerm, setSearchTerm] = useState("");
  const debouncedSearchTerm = useDebounce(searchTerm, 200); // debounce by 200ms

  // Filter agents based on search term
  const filteredAgents = useMemo(() => {
    return agents.filter((agent) =>
      agent?.name?.toLowerCase().includes(debouncedSearchTerm.toLowerCase())
    );
  }, [agents, debouncedSearchTerm]);

  return (
    <div className="max-w-3xl mx-auto py-6">
      {/* Selected Gallery */}
      <div className="flex justify-between items-center mb-6 mx-6">
        <div className="flex items-center space-x-2">
          <Icon name="galleryIcon" className="text-[#666666]" size={22} />
          <h1 className="text-base font-medium text-[#666666]">
            Gallery: {selectedGallery}
          </h1>
        </div>
        <button
          onClick={() => onChangeGallery()}
          className="text-teal-600 underline py-2 px-4 rounded-xl hover:bg-teal-50 transition-colors"
        >
          Change
        </button>
      </div>

      {/* Search */}
      <div className="relative mx-6 mb-2">
        <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
          <Icon name="search" className="h-4 w-4 text-gray-500" />
        </div>
        <input
          type="text"
          placeholder="Search Gallery"
          className="w-full py-2 pl-10 bg-gray-50 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-teal-500"
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
        />
      </div>

      {/* Agents */}
      <div className="max-h-[325px] h-full overflow-y-auto">
        {filteredAgents.map((agent) => (
          <ListItem
            key={agent?.id || ""}
            name={agent?.name || ""}
            enabled={agent.enabled}
            onToggle={() => onToggleAgent(agent?.id || "")}
          />
        ))}
      </div>
    </div>
  );
};

export default AgentsModalScreen;
