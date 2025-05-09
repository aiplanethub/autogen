import React, { useMemo, useState } from "react";
import Icon from "../../../Icon";
import useDebounce from "../../../utils/utils";
import ListItem from "./ListItem";

interface Tool {
  id: string;
  name: string;
  enabled: boolean;
}

const ToolsModalScreen = () => {
  const [searchTerm, setSearchTerm] = useState("");
  const [tools, setTools] = useState<Tool[]>([
    { id: "calculator", name: "Calculator Tool", enabled: false },
    { id: "imageGeneration", name: "Image Generation Tool", enabled: false },
    { id: "fetchWebpage", name: "Fetch Webpage Tool", enabled: false },
    { id: "bingSearch", name: "Bing Search Tool", enabled: false },
    { id: "googleSearch", name: "Google Search Tool", enabled: false },
  ]);

  const onToggle = (id: string) => {
    setTools(
      tools.map((tool) =>
        tool.id === id ? { ...tool, enabled: !tool.enabled } : tool
      )
    );
  };

  const debouncedSearchTerm = useDebounce(searchTerm, 200); // debounce by 200ms

  // Filter galleries based on search term
  const filteredTools = useMemo(() => {
    return tools.filter((tool) =>
      tool.name.toLowerCase().includes(debouncedSearchTerm.toLowerCase())
    );
  }, [debouncedSearchTerm]);

  return (
    <div className="max-w-3xl mx-auto py-6">
      {/* Selected Gallery */}
      <div className="flex justify-between items-center mb-6 mx-6">
        <div className="flex items-center space-x-2">
          <Icon name="galleryIcon" className="text-[#666666]" size={22} />
          <h1 className="text-base font-medium text-[#666666]">
            Gallery: New Project
          </h1>
        </div>
        <button className="text-teal-600 underline py-2 px-4 rounded-xl hover:bg-teal-50 transition-colors">
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

      {/* Tools */}
      <div className="max-h-[325px] h-full overflow-y-auto">
        {filteredTools.map((tool) => (
          <ListItem
            key={tool.id}
            name={tool.name}
            enabled={tool.enabled}
            onToggle={() => onToggle(tool.id)}
          />
        ))}
      </div>
    </div>
  );
};

export default ToolsModalScreen;
