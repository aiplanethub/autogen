import { Switch } from "@headlessui/react";
import React from "react";

interface ToolItemProps {
  name: string;
  enabled: boolean;
  onToggle: () => void;
}

const ListItem: React.FC<ToolItemProps> = ({ name, enabled, onToggle }) => {
  return (
    <div className="flex items-center justify-between py-5 border-b border-gray-100 px-8">
      <h3 className="text-base font-medium">{name}</h3>
      <Switch
        checked={enabled}
        onChange={onToggle}
        className="group inline-flex h-5 w-9 items-center rounded-full bg-gray-200 transition data-[checked]:bg-[#115E59]"
      >
        <span className="size-3 translate-x-1 rounded-full bg-white transition group-data-[checked]:translate-x-5" />
      </Switch>
    </div>
  );
};

export default ListItem;
