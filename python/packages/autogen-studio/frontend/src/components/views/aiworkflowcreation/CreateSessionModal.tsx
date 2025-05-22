import React, { Fragment, useState } from "react";
import { X } from "lucide-react";
import {
  Button,
  Dialog,
  DialogPanel,
  DialogTitle,
  Transition,
  TransitionChild,
} from "@headlessui/react";

interface CreateSessionModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSaveSession: (sessionName: string) => Promise<void>;
}

const CreateSessionModal: React.FC<CreateSessionModalProps> = ({
  isOpen,
  onClose,
  onSaveSession,
}) => {
  const [isLoading, setIsLoading] = useState(false);
  const [sessionName, setSessionName] = useState("");
  const [sessionNameError, setSessionNameError] = useState("");

  const handleSubmit = () => {
    // Validate session name
    if (!sessionName.trim()) {
      setSessionNameError("Please enter a session name.");
      return;
    }
    setIsLoading(true);
    onSaveSession(sessionName);
    setIsLoading(false);
    onClose();
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
                </div>

                <div className="mt-8 flex justify-end">
                  <Button
                    disabled={isLoading}
                    onClick={handleSubmit}
                    className="bg-blue-600 hover:bg-blue-700 text-white font-medium py-2 px-6 rounded-lg text-base"
                  >
                    Get Started
                  </Button>
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
