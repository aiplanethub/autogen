import React, { useState } from "react";
import { X } from "lucide-react";
import { Dialog, DialogTitle, DialogPanel } from "@headlessui/react";
import IndustrySelector from "./IndustrySelector";
import { message } from "antd";
import { IPrompt, PromptCategory } from "../../../../types/aiworkflowcreation";

interface PromptModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSavePrompt: (prompt: IPrompt) => void;
}

const CreatePromptModal: React.FC<PromptModalProps> = ({
  isOpen,
  onClose,
  onSavePrompt,
}) => {
  const [messageApi, contextHolder] = message.useMessage();
  const [selectedIndustry, setSelectedIndustry] =
    useState<PromptCategory>("EDUCATION");
  const [promptInstructions, setPromptInstructions] = useState("");
  const [isDropdownOpen, setIsDropdownOpen] = useState(false);

  const handleSavePrompt = () => {
    // Validation: Cannot save with empty prompt or without category
    if (!selectedIndustry) {
      messageApi.error("Please select an industry");
      return;
    }

    if (!promptInstructions.trim()) {
      messageApi.error("Prompt instructions cannot be empty");
      return;
    }

    onSavePrompt({
      id: "",
      category: selectedIndustry,
      content: promptInstructions,
    });

    // Save logic would go here
    console.log("Saving prompt:", {
      industry: selectedIndustry,
      instructions: promptInstructions,
    });
    messageApi.success("Prompt saved successfully!");
    onClose();
  };

  return (
    <Dialog open={isOpen} onClose={onClose} className="relative z-50">
      {contextHolder}
      <div
        className="fixed inset-0 bg-black/30 dark:bg-black/60"
        aria-hidden="true"
      />

      <div className="fixed inset-0 flex items-center justify-center p-4">
        <DialogPanel className="w-full max-w-md transform overflow-hidden rounded-2xl bg-primary p-6 shadow-xl transition-all">
          <div className="flex justify-between items-center mb-8">
            <DialogTitle className="text-xl text-primary font-semibold">
              Create Prompt
            </DialogTitle>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-600"
            >
              <X size={24} />
            </button>
          </div>

          <div className="space-y-6">
            <div>
              <label className="block text-base text-primary font-medium mb-2">
                Select Industry
              </label>
              <IndustrySelector
                selectedIndustry={selectedIndustry}
                setSelectedIndustry={setSelectedIndustry}
                isOpen={isDropdownOpen}
                setIsOpen={setIsDropdownOpen}
              />
            </div>

            <div>
              <label className="block text-base text-primary font-medium mb-2">
                Prompt Instructions
              </label>
              <textarea
                className="w-full border bg-primary text-primary border-secondary rounded-lg p-4 min-h-[150px] focus:ring-2 outline-none focus:ring-[#115E59] focus:border-transparent"
                placeholder="Enter your prompt instructions here..."
                value={promptInstructions}
                onChange={(e) => setPromptInstructions(e.target.value)}
              />
            </div>

            <div className="flex justify-end mt-6">
              <button
                onClick={handleSavePrompt}
                className="px-6 py-2 bg-[#115E59] text-white font-medium text-base rounded-lg hover:bg-teal-700 transition-colors"
              >
                Save Prompt
              </button>
            </div>
          </div>
        </DialogPanel>
      </div>
    </Dialog>
  );
};

export default CreatePromptModal;
