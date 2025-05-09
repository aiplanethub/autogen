import * as React from "react";
import Layout from "../components/layout";
import { graphql } from "gatsby";
import AIWorkflowCreationManager from "../components/views/aiworkflowcreation/manager";

// markup
const AIWorkflowCreationPage = ({ data }: any) => {
  return (
    <Layout
      meta={data.site.siteMetadata}
      title="Home"
      link={"/aiworkflowcreation"}
    >
      <main style={{ height: "100%" }} className=" h-full ">
        <AIWorkflowCreationManager />
      </main>
    </Layout>
  );
};

export const query = graphql`
  query HomePageQuery {
    site {
      siteMetadata {
        description
        title
      }
    }
  }
`;

export default AIWorkflowCreationPage;
