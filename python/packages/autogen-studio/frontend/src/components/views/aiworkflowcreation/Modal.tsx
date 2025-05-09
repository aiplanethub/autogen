import React from "react";
import { Dialog } from "@headlessui/react";
import { X } from "lucide-react";

interface ModalProps {
  isOpen: boolean;
  onClose: () => void;
  title: string;
  children: React.ReactNode;
}

const Modal: React.FC<ModalProps> = ({ isOpen, onClose, title, children }) => {
  return (
    <Dialog open={isOpen} onClose={onClose}>
      <div className="fixed inset-0 flex items-center justify-center bg-black/10 z-50">
        <div className="w-full max-w-lg bg-white rounded-xl shadow-lg overflow-hidden">
          {/* Header */}
          <div className="flex justify-between items-center py-4 px-6 border-b">
            <h2 className="text-lg font-semibold capitalize">{title}</h2>
            <button
              onClick={onClose}
              className="text-gray-500 hover:text-gray-700"
            >
              <X size={22} />
            </button>
          </div>

          {/* Content */}
          {children}
        </div>
      </div>
    </Dialog>
  );
};

export default Modal;
