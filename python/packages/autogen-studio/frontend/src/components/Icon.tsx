import React from "react";
import { iconsMap, IconName } from "../icons/iconsMap";

interface IconProps {
  name: IconName;
  size?: number;
  className?: string;
  strokeWidth?: number;
}

const Icon: React.FC<IconProps> = ({
  name,
  size = 24,
  className = "",
  strokeWidth = 2,
}) => {
  const LucideIcon = iconsMap[name];

  if (!LucideIcon) {
    console.warn(`Icon "${name}" does not exist in iconsMap.`);
    return null;
  }

  return (
    <LucideIcon size={size} strokeWidth={strokeWidth} className={className} />
  );
};

export default Icon;
