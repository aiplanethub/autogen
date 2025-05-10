import React from "react";
import { IconName } from "../../../../../icons/iconsMap";
import Icon from "../../../../Icon";

interface CategoryButtonProps {
  icon: IconName;
  label: string;
  active?: boolean;
  onClick: () => void;
}

const CategoryButton: React.FC<CategoryButtonProps> = ({
  icon,
  label,
  active = false,
  onClick,
}) => {
  return (
    <button
      className={`w-full flex items-center px-3 py-2 rounded-md text-left ${
        active ? "bg-secondary" : "hover:bg-tertiary"
      }`}
      onClick={onClick}
    >
      <Icon
        name={icon}
        className={`mr-3 h-5 w-5 ${active ? "text-primary" : "text-secondary"}`}
      />
      <span
        className={`text-sm ${
          active ? "font-medium text-primary" : "text-secondary"
        }`}
      >
        {label}
      </span>
    </button>
  );
};

export default CategoryButton;
