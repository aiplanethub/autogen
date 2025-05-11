import React, { Fragment, useEffect, useState } from "react";
import { X, ChevronDown, Check } from "lucide-react";
import {
  Dialog,
  DialogPanel,
  DialogTitle,
  Listbox,
  ListboxOptions,
  ListboxOption,
  ListboxButton,
  Transition,
  TransitionChild,
} from "@headlessui/react";
import { IAIWorkflowCreationKB } from "../../types/aiworkflowcreation";
import { cn } from "../../utils/utils";

interface CreateSessionModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSaveSession: (
    sessionName: string,
    knowledgeBase: IAIWorkflowCreationKB
  ) => void;
}

const CreateSessionModal: React.FC<CreateSessionModalProps> = ({
  isOpen,
  onClose,
  onSaveSession,
}) => {
  const [sessionName, setSessionName] = useState("");
  const [selectedKnowledgeBase, setSelectedKnowledgeBase] =
    useState<IAIWorkflowCreationKB | null>(null);
  const [knowledgeBases, setKnowledgeBases] = useState<
    Array<IAIWorkflowCreationKB>
  >([]);
  const [sessionNameError, setSessionNameError] = useState("");
  const [kbError, setKBError] = useState("");

  useEffect(() => {
    const fetchKnowledgeBases = () => {
      const data = [
        {
          id: "kb1",
          name: "KB1",
        },
        {
          id: "kb2",
          name: "KB2",
        },
        {
          id: "kb3",
          name: "KB3",
        },
        {
          id: "kb4",
          name: "KB4",
        },
      ];
      setKnowledgeBases(data);
    };

    fetchKnowledgeBases();
  }, []);

  const handleSubmit = () => {
    // Validate session name
    if (!sessionName.trim()) {
      setSessionNameError("Please enter a session name.");
      return;
    }

    if (selectedKnowledgeBase === null) {
      setKBError("Please select a knowledgebase.");
      return;
    }

    onSaveSession(sessionName, selectedKnowledgeBase);
    onClose();
  };

  const onChange = (value: string) => {
    const knowledgebase = knowledgeBases.find((kb) => kb.id === value);
    if (!!knowledgebase) setSelectedKnowledgeBase(knowledgebase);
    return;
  };

  return (
    <Transition appear show={isOpen} as={Fragment}>
      <Dialog as="div" className="relative z-50" onClose={onClose}>
        <TransitionChild
          as={Fragment}
          enter="ease-out duration-300"
          enterFrom="opacity-0"
          enterTo="opacity-100"
          leave="ease-in duration-200"
          leaveFrom="opacity-100"
          leaveTo="opacity-0"
        >
          <div className="fixed inset-0 bg-black bg-opacity-80" />
        </TransitionChild>

        <div className="fixed inset-0 overflow-y-auto">
          <div className="flex min-h-full items-center justify-center p-4 text-center">
            <TransitionChild
              as={Fragment}
              enter="ease-out duration-300"
              enterFrom="opacity-0 scale-95"
              enterTo="opacity-100 scale-100"
              leave="ease-in duration-200"
              leaveFrom="opacity-100 scale-100"
              leaveTo="opacity-0 scale-95"
            >
              <DialogPanel
                className="w-full max-w-md transform rounded-lg bg-primary p-6 text-left align-middle shadow-xl transition-all"
                onClick={(e) => e.stopPropagation()}
              >
                <div className="flex justify-between items-center">
                  <DialogTitle
                    as="h3"
                    className="text-xl font-bold text-primary"
                  >
                    Create Session
                  </DialogTitle>
                  <button
                    type="button"
                    className="text-gray-400 hover:text-gray-500 focus:outline-none"
                    onClick={onClose}
                  >
                    <X className="h-5 w-5" aria-hidden="true" />
                  </button>
                </div>

                <div className="space-y-6 mt-6">
                  {/* Session Name Input */}
                  <div>
                    <label
                      htmlFor="sessionName"
                      className="block text-base text-primary font-medium mb-2"
                    >
                      Session Name
                    </label>
                    <div className="relative">
                      <input
                        type="text"
                        id="sessionName"
                        value={sessionName}
                        onChange={(e) => {
                          setSessionName(e.target.value);
                          if (!!sessionNameError) {
                            setSessionNameError("");
                          }
                        }}
                        placeholder="Enter a session name"
                        className={`w-full p-3 border bg-primary text-primary text-sm ${
                          sessionNameError
                            ? "border-red-500"
                            : "border-secondary"
                        } rounded-lg`}
                      />
                      {sessionNameError && (
                        <p className="mt-1 text-sm text-red-500">
                          {sessionNameError}
                        </p>
                      )}
                    </div>
                  </div>

                  {/* Knowledge Base Select */}
                  <div>
                    <label
                      htmlFor="knowledgeBase"
                      className="block text-base font-medium mb-2 text-primary"
                    >
                      Knowledge Base
                    </label>
                    <Listbox
                      value={
                        !!selectedKnowledgeBase?.id
                          ? selectedKnowledgeBase?.id
                          : ""
                      }
                      onChange={(value) => {
                        onChange(value);
                        if (!!kbError) {
                          setKBError("");
                        }
                      }}
                    >
                      <div className="relative mt-1">
                        <ListboxButton
                          className={cn(
                            "relative w-full h-full p-3 bg-primary border rounded-lg text-left text-sm",
                            kbError ? "border-red-500" : "border-secondary"
                          )}
                        >
                          {!!selectedKnowledgeBase?.name ? (
                            <span className="block truncate text-primary">
                              {selectedKnowledgeBase?.name}
                            </span>
                          ) : (
                            <span className="block truncate text-gray-400">
                              Select a knowledge base
                            </span>
                          )}

                          <span className="pointer-events-none absolute inset-y-0 right-0 flex items-center pr-2">
                            <ChevronDown
                              className="h-5 w-5 text-gray-400"
                              aria-hidden="true"
                            />
                          </span>
                        </ListboxButton>
                        <Transition
                          as={Fragment}
                          leave="transition ease-in duration-100"
                          leaveFrom="opacity-100"
                          leaveTo="opacity-0"
                        >
                          <ListboxOptions className="absolute z-50 mt-1 max-h-60 w-full overflow-auto rounded-md bg-secondary py-1 text-base shadow-lg ring-1 ring-black ring-opacity-5 focus:outline-none sm:text-sm">
                            {knowledgeBases.map((kb, kbIdx) => (
                              <ListboxOption
                                key={kb.id}
                                className={({ active }) =>
                                  `relative cursor-default select-none py-2 pl-10 pr-4 ${
                                    active
                                      ? "bg-blue-100 text-blue-900"
                                      : "text-primary"
                                  }`
                                }
                                value={kb.id}
                              >
                                {({ selected }) => (
                                  <>
                                    <span
                                      className={`block truncate ${
                                        selected ? "font-medium" : "font-normal"
                                      }`}
                                    >
                                      {kb.name}
                                    </span>
                                    {selected ? (
                                      <span className="absolute inset-y-0 left-0 flex items-center pl-3 text-blue-600">
                                        <Check
                                          className="h-5 w-5"
                                          aria-hidden="true"
                                        />
                                      </span>
                                    ) : null}
                                  </>
                                )}
                              </ListboxOption>
                            ))}
                          </ListboxOptions>
                        </Transition>
                      </div>
                    </Listbox>
                    {kbError && (
                      <p className="mt-1 text-sm text-red-500">{kbError}</p>
                    )}
                  </div>
                </div>

                <div className="mt-8 flex justify-end">
                  <button
                    type="button"
                    onClick={handleSubmit}
                    className="bg-blue-600 hover:bg-blue-700 text-white font-medium py-2 px-6 rounded-lg text-base"
                  >
                    Get Started
                  </button>
                </div>
              </DialogPanel>
            </TransitionChild>
          </div>
        </div>
      </Dialog>
    </Transition>
  );
};

export default CreateSessionModal;
