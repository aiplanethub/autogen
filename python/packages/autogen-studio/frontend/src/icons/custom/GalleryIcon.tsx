import React from "react";

interface CustomIconProps extends React.SVGProps<SVGSVGElement> {
  size?: number;
}

const GalleryIcon: React.FC<CustomIconProps> = ({ size = 24, ...props }) => {
  return (
    <svg
      {...props}
      xmlns="http://www.w3.org/2000/svg"
      width={size}
      height={size}
      viewBox="0 0 17 17"
      fill="none"
    >
      <path
        d="M6.1875 3.26496V14.735C6.1875 15.2956 6.64191 15.75 7.20246 15.75H14.1725C14.7331 15.75 15.1875 15.2956 15.1875 14.735V3.26496C15.1875 2.70441 14.7331 2.25 14.1725 2.25H7.20246C6.64191 2.25 6.1875 2.70441 6.1875 3.26496Z"
        stroke="currentColor"
        stroke-width="1.125"
        stroke-linejoin="round"
      />
      <path
        d="M2.8125 12.9375V5.0625V12.9375ZM4.5 14.0625V3.9375V14.0625Z"
        fill="currentColor"
      />
      <path
        d="M2.8125 12.9375V5.0625M4.5 14.0625V3.9375"
        stroke="currentColor"
        stroke-width="1.125"
        stroke-miterlimit="10"
        stroke-linecap="round"
      />
    </svg>
  );
};

export default GalleryIcon;
