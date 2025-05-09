import React, { useMemo, useState } from "react";
import useDebounce, { cn } from "../../utils/utils";
import Icon from "../../Icon";
import { IGalleryProps } from "../../types/aiworkflowcreation";

interface GallerySelectorProps {
  galleries: Array<IGalleryProps>;
  onSelectGallery: (gallery: IGalleryProps) => void;
  selectedGallery: IGalleryProps | null;
}

const GalleryModalScreen: React.FC<GallerySelectorProps> = ({
  galleries,
  onSelectGallery,
  selectedGallery,
}) => {
  const [searchTerm, setSearchTerm] = useState("");
  const debouncedSearchTerm = useDebounce(searchTerm, 200); // debounce by 200ms

  // Filter galleries based on search term
  const filteredGalleries = useMemo(() => {
    return galleries.filter((gallery) =>
      gallery.name.toLowerCase().includes(debouncedSearchTerm.toLowerCase())
    );
  }, [debouncedSearchTerm]);

  return (
    <div className="p-6">
      {/* Search */}
      <div className="relative mb-6">
        <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
          <Icon name="search" className="h-4 w-4 text-gray-500" />
        </div>
        <input
          type="text"
          placeholder="Search Gallery"
          className="w-full py-2 pl-10 bg-gray-50 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-teal-500"
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
        />
      </div>

      {/* Create New Gallery Button */}
      <button className="flex items-center text-base pl-1 font-medium mb-6 text-teal-700 hover:text-teal-800">
        Create New Gallery
        <Icon name="plus" className="ml-1" size={18} />
      </button>

      {/* Gallery List */}
      <div
        className={cn(
          "space-y-3 max-h-[270px] overflow-y-auto",
          filteredGalleries.length > 4 && "pr-3"
        )}
      >
        {filteredGalleries.map((gallery) => (
          <button
            key={gallery.id}
            className={cn(
              "w-full flex items-center p-4 rounded-lg transition",
              gallery.id === selectedGallery?.id
                ? "bg-gray-100 border border-teal-700 text-teal-700"
                : "hover:bg-gray-50 border border-gray-200"
            )}
            onClick={() => onSelectGallery(gallery)}
          >
            <Icon
              name="galleryIcon"
              size={24}
              className={cn(
                "mr-3",
                gallery.id === selectedGallery?.id
                  ? "text-teal-700"
                  : "text-gray-500"
              )}
            />
            <span className="text-sm font-normal">{gallery.name}</span>
          </button>
        ))}
      </div>
    </div>
  );
};

export default GalleryModalScreen;
