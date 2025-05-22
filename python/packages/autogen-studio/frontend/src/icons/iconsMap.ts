import {
  Search,
  Plus,
  Paperclip,
  Sparkles,
  Users,
  Send,
  BookOpen,
  Building,
  TrendingUp,
  LayoutGrid,
  X,
  ChevronRight,
  Brain,
} from "lucide-react";
import GalleryIcon from "./custom/GalleryIcon";

export const iconsMap = {
  galleryIcon: GalleryIcon,
  search: Search,
  plus: Plus,
  paperclip: Paperclip,
  sparkles: Sparkles,
  users: Users,
  send: Send,
  bookopen: BookOpen,
  building: Building,
  trendingup: TrendingUp,
  layoutgrid: LayoutGrid,
  x: X,
  chevronright: ChevronRight,
  brain: Brain,
} as const;

export type IconName = keyof typeof iconsMap;
