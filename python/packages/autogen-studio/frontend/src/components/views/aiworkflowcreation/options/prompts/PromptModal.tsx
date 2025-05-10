import React, { useMemo, useState } from "react";
import { Search } from "lucide-react";
import PromptCard from "./PromptCard";
import CategoryButton from "./CategoryButton";
import Icon from "../../../../Icon";
import { IPrompt } from "../../../../types/aiworkflowcreation";
import CreatePromptModal from "./CreatePromptModal";
import useDebounce from "../../../../utils/utils";

const PromptModal: React.FC<{
  isOpen: boolean;
  onClose: () => void;
  selectedPrompt: IPrompt | null;
  onSelectPrompt: (prompt: IPrompt) => void;
}> = ({ isOpen, onClose, selectedPrompt, onSelectPrompt }) => {
  const [activeCategory, setActiveCategory] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [isCreatePromptModalOpen, setIsCreatePromptModalOpen] = useState(false);

  const [samplePrompts, setSamplePrompts] = useState<Array<IPrompt>>([
    {
      id: "1",
      category: "MARKETING",
      content:
        "Help me create a project timeline for the project I'm developing. The design has to be finished and signed of by the Product Manager, we have to do User Research, Handoff the concept to the development team and let them code the app.",
    },
    {
      id: "2",
      category: "EDUCATION",
      content:
        "Help me create a project timeline for the project I'm developing. The design has to be finished and signed of by the Product Manager, we have to do User Research, Handoff the concept to the development team and let them code the app.",
    },
    {
      id: "3",
      category: "BANKING",
      content:
        "Help me create a project timeline for the project I'm developing. The design has to be finished and signed of by the Product Manager, we have to do User Research, Handoff the concept to the development team and let them code the app.",
    },
    {
      id: "4",
      category: "MARKETING",
      content:
        "Help me create a project timeline for the project I'm developing. The design has to be finished and signed of by the Product Manager, we have to do User Research, Handoff the concept to the development team and let them code the app.",
    },
    {
      id: "5",
      category: "EDUCATION",
      content:
        "Help me create a project timeline for the project I'm developing. The design has to be finished and signed of by the Product Manager, we have to do User Research, Handoff the concept to the development team and let them code the app.",
    },
    {
      id: "6",
      category: "BANKING",
      content:
        "Help me create a project timeline for the project I'm developing. The design has to be finished and signed of by the Product Manager, we have to do User Research, Handoff the concept to the development team and let them code the app.",
    },
    {
      id: "7",
      category: "MARKETING",
      content:
        "Help me create a project timeline for the project I'm developing. The design has to be finished and signed of by the Product Manager, we have to do User Research, Handoff the concept to the development team and let them code the app.",
    },
    {
      id: "8",
      category: "EDUCATION",
      content:
        "Help me create a project timeline for the project I'm developing. The design has to be finished and signed of by the Product Manager, we have to do User Research, Handoff the concept to the development team and let them code the app.",
    },
    {
      id: "9",
      category: "BANKING",
      content:
        "Help me create a project timeline for the project I'm developing. The design has to be finished and signed of by the Product Manager, we have to do User Research, Handoff the concept to the development team and let them code the app.",
    },
  ]);

  const debouncedSearchTerm = useDebounce(searchQuery, 200); // debounce by 200ms

  const filteredPrompts = useMemo(() => {
    return samplePrompts.filter((prompt) => {
      const matchesCategory = activeCategory
        ? prompt.category === activeCategory
        : true;
      const matchesSearch =
        searchQuery === "" ||
        prompt.content.toLowerCase().includes(searchQuery.toLowerCase());
      return matchesCategory && matchesSearch;
    });
  }, [samplePrompts, activeCategory, debouncedSearchTerm]);

  const onSavePrompt = (prompt: IPrompt) => {
    setSamplePrompts([
      ...samplePrompts,
      { ...prompt, id: `${samplePrompts.length + 1}` },
    ]);
    setIsCreatePromptModalOpen(false);
  };

  return (
    <>
      {isOpen && (
        <div className="fixed inset-0 bg-black bg-opacity-50 dark:bg-opacity-70 flex items-center justify-center z-50">
          <div className="rounded-xl bg-primary w-full max-w-5xl h-[80vh] overflow-hidden flex">
            {/* Sidebar */}
            <div className="w-64 border-r border-secondary p-5 flex flex-col ">
              <h2 className="text-2xl font-semibold mb-5">Prompts</h2>

              {/* Create Prompt Button */}
              <button
                onClick={() => setIsCreatePromptModalOpen(true)}
                className="bg-[#115E59] hover:bg-green-800 text-white font-normal text-base px-4 py-2 rounded-lg mb-5 flex items-center justify-center"
              >
                <span>Create Prompt</span>
                <Icon name="plus" size={20} className="ml-2" />
              </button>

              {/* Category Navigation */}
              <div>
                <h3 className="text-sm font-medium text-gray-500 mb-3">
                  By Industries
                </h3>

                <div className="space-y-2">
                  <CategoryButton
                    icon="layoutgrid"
                    label="All Use Cases"
                    onClick={() => setActiveCategory(null)}
                    active={activeCategory === null}
                  />
                  <CategoryButton
                    icon="bookopen"
                    label="Education"
                    onClick={() => setActiveCategory("EDUCATION")}
                    active={activeCategory === "EDUCATION"}
                  />
                  <CategoryButton
                    icon="building"
                    label="Banking"
                    onClick={() => setActiveCategory("BANKING")}
                    active={activeCategory === "BANKING"}
                  />
                  <CategoryButton
                    icon="trendingup"
                    label="Marketing"
                    onClick={() => setActiveCategory("MARKETING")}
                    active={activeCategory === "MARKETING"}
                  />
                </div>
              </div>
            </div>

            {/* Main Content Area */}
            <div className="flex-1 flex flex-col overflow-hidden">
              {/* Search Bar */}
              <div className="p-5 border-b border-secondary">
                <div className="relative">
                  <div className="absolute inset-y-0 left-0 flex items-center pl-3 pointer-events-none">
                    <Search className="h-5 w-5 text-gray-400" />
                  </div>
                  <input
                    type="text"
                    placeholder="Search prompts"
                    className="block w-full pl-10 pr-3 py-2 border border-secondary rounded-lg focus:ring-blue-500 focus:border-blue-500 outline-none bg-primary"
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                  />
                </div>
              </div>

              {/* Prompt Grid */}
              <div className="flex-1 overflow-y-auto p-5">
                <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
                  {filteredPrompts.map((prompt) => (
                    <PromptCard
                      key={prompt.id}
                      category={prompt.category}
                      content={prompt.content}
                      isPromptSelected={
                        !!selectedPrompt
                          ? selectedPrompt.id === prompt.id
                          : false
                      }
                      onSelectPrompt={() => onSelectPrompt(prompt)}
                    />
                  ))}
                </div>
              </div>
            </div>

            {/* Close Button */}
            <button
              onClick={() => onClose()}
              className="absolute top-5 right-5 text-white hover:text-gray-200"
            >
              <Icon name="x" size={20} />
            </button>
          </div>

          {isCreatePromptModalOpen && (
            <CreatePromptModal
              isOpen={isCreatePromptModalOpen}
              onClose={() => setIsCreatePromptModalOpen(false)}
              onSavePrompt={onSavePrompt}
            />
          )}
        </div>
      )}
    </>
  );
};

export default PromptModal;
