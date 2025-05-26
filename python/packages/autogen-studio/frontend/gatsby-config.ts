import { GatsbyConfig } from "gatsby";
import path from "path";
import fs from "fs"

const envFile = `.env.${process.env.NODE_ENV}`;
const envPath = path.resolve(process.cwd(), envFile);

console.log('GATSBY_API_URL:', process.env.GATSBY_API_URL);
console.log('NODE_ENV:', process.env.NODE_ENV);
// Check if file exists synchronously
if (fs.existsSync(envPath)) {
  require("dotenv").config({
    path: envPath,
  });
} else {
  console.warn(`File '${envFile}' is missing. Using default values.`);
  // Fallback to default .env file
  require("dotenv").config();
}

const config: GatsbyConfig = {
  pathPrefix: process.env.PREFIX_PATH_VALUE || "",
  siteMetadata: {
    title: `AutoGen Studio`,
    description: `Build Multi-Agent Apps`,
    siteUrl: `http://tbd.place`,
  },
  // More easily incorporate content into your pages through automatic TypeScript type generation and better GraphQL IntelliSense.
  // If you use VSCode you can also use the GraphQL plugin
  // Learn more at: https://gatsby.dev/graphql-typegen
  graphqlTypegen: true,
  plugins: [
    "gatsby-plugin-postcss",
    "gatsby-plugin-image",
    "gatsby-plugin-sitemap",
    {
      resolve: "gatsby-plugin-manifest",
      options: {
        icon: "src/images/icon.png",
      },
    },
    "gatsby-plugin-mdx",
    "gatsby-plugin-sharp",
    "gatsby-transformer-sharp",
    {
      resolve: "gatsby-source-filesystem",
      options: {
        name: "images",
        path: "./src/images/",
      },
      __key: "images",
    },
    {
      resolve: "gatsby-source-filesystem",
      options: {
        name: "pages",
        path: "./src/pages/",
      },
      __key: "pages",
    },
  ],
};

export default config;
