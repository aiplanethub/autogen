import React from "react";
import { cn } from "../../../../utils/utils";

interface PromptCardProps {
  category: "MARKETING" | "EDUCATION" | "BANKING";
  content: string;
  onSelectPrompt: () => void;
  isPromptSelected: boolean;
}

const PromptCard: React.FC<PromptCardProps> = ({
  category,
  content,
  onSelectPrompt,
  isPromptSelected,
}) => {
  // Define category badge styles and icons
  const categoryConfig = {
    MARKETING: {
      bgColor: "bg-blue-100",
      textColor: "text-blue-800",
      icon: "📊",
    },
    EDUCATION: {
      bgColor: "bg-amber-100",
      textColor: "text-amber-800",
      icon: "📚",
    },
    BANKING: {
      bgColor: "bg-green-100",
      textColor: "text-green-800",
      icon: "🏦",
    },
  };

  const config = categoryConfig[category];

  return (
    <div
      className={cn(
        "border border-secondary rounded-lg p-4 hover:shadow-md transition-shadow cursor-pointer",
        isPromptSelected && "border-green-600 border-2"
      )}
      onClick={() => onSelectPrompt()}
    >
      {/* Category Badge */}
      <div
        className={`inline-flex items-center px-2.5 py-0.5 rounded-md text-xs font-medium ${config.bgColor} ${config.textColor} mb-3`}
      >
        <span className="mr-1">{config.icon}</span>
        <span>{category}</span>
      </div>

      {/* Prompt Content */}
      <p className="text-sm">{content}</p>
    </div>
  );
};

export default PromptCard;
