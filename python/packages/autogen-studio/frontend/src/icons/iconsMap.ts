import { Search, Plus, Paperclip, Sparkles, Users, Send } from "lucide-react";
import GalleryIcon from "./custom/GalleryIcon";

export const iconsMap = {
  galleryIcon: GalleryIcon,
  search: Search,
  plus: Plus,
  paperclip: Paperclip,
  sparkles: Sparkles,
  users: Users,
  send: Send,
} as const;

export type IconName = keyof typeof iconsMap;
