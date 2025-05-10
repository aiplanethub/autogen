import React, { Fragment } from "react";
import {
  Listbox,
  Transition,
  ListboxButton,
  ListboxOption,
  ListboxOptions,
} from "@headlessui/react";
import { ChevronDown } from "lucide-react";
import { cn } from "../../../../utils/utils";
import { PromptCategory } from "../../../../types/aiworkflowcreation";

const industries = [
  { id: "MARKETING", name: "MARKETING", icon: "📊", color: "bg-blue-100" },
  { id: "BANKING", name: "BANKING", icon: "🏦", color: "bg-green-100" },
  { id: "EDUCATION", name: "EDUCATION", icon: "📚", color: "bg-amber-100" },
];

interface IndustrySelectorProps {
  selectedIndustry: PromptCategory | null;
  setSelectedIndustry: (industry: PromptCategory) => void;
  isOpen: boolean;
  setIsOpen: (isOpen: boolean) => void;
}

const IndustrySelector: React.FC<IndustrySelectorProps> = ({
  selectedIndustry,
  setSelectedIndustry,
  isOpen,
  setIsOpen,
}) => {
  const selectedIndustryObj = selectedIndustry
    ? industries.find((industry) => industry.id === selectedIndustry)
    : null;

  return (
    <Listbox value={selectedIndustry} onChange={setSelectedIndustry}>
      <div className="relative">
        <ListboxButton
          className="relative w-full py-3 pl-4 pr-10 text-left bg-primary border border-secondary rounded-lg cursor-pointer focus:outline-none focus:ring-2 focus:ring-[#115E59]"
          onClick={() => setIsOpen(!isOpen)}
        >
          <span className="flex items-center">
            {selectedIndustryObj ? (
              <span
                className={cn(
                  "flex item-center py-1 px-3 rounded-xl",
                  selectedIndustryObj.color
                )}
              >
                <span className="mr-2 text-xs">{selectedIndustryObj.icon}</span>
                <span className="block truncate text-xs font-medium">
                  {selectedIndustryObj.name}
                </span>
              </span>
            ) : (
              <span className="block truncate text-gray-500">
                Select an industry
              </span>
            )}
          </span>
          <span className="absolute inset-y-0 right-0 flex items-center pr-2 pointer-events-none">
            <ChevronDown size={20} className="text-gray-400" />
          </span>
        </ListboxButton>

        <Transition
          as={Fragment}
          leave="transition ease-in duration-100"
          leaveFrom="opacity-100"
          leaveTo="opacity-0"
          show={isOpen}
        >
          <ListboxOptions
            className="absolute w-full py-1 mt-1 overflow-auto bg-primary border border-secondary rounded-md shadow-lg max-h-60 ring-1 ring-black ring-opacity-5 focus:outline-none z-10"
            static
          >
            {industries.map((industry) => (
              <ListboxOption
                key={industry.id}
                className={({ active }) =>
                  `${
                    active ? "bg-secondary" : "hover:bg-tertiary"
                  } cursor-default select-none relative py-2 pl-4 pr-10 text-primary`
                }
                value={industry.id}
                onClick={() => setIsOpen(false)}
              >
                {({ selected, active }) => (
                  <>
                    <div className="flex items-center">
                      <span className="mr-3 text-sm">{industry.icon}</span>
                      <span
                        className={` text-sm ${
                          selected ? "font-medium" : "font-normal"
                        } block truncate`}
                      >
                        {industry.name}
                      </span>
                    </div>
                  </>
                )}
              </ListboxOption>
            ))}
          </ListboxOptions>
        </Transition>
      </div>
    </Listbox>
  );
};

export default IndustrySelector;
