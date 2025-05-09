import GalleryIcon from "./custom/GalleryIcon";

export const iconsMap = { galleryIcon: GalleryIcon } as const;

export type IconName = keyof typeof iconsMap;
