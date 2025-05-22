import { IAIWorkflowCreationSession } from "../../types/aiworkflowcreation";
import { BaseAPI } from "../../utils/baseapi";

export class AIWorkflowCreationAPI extends BaseAPI {
  async listAIWorkflowCreationSessions(
    userId: string
  ): Promise<Array<IAIWorkflowCreationSession>> {
    const response = await fetch(
      `${this.getBaseUrl()}/builder-session?user_id=${userId}`,
      {
        headers: this.getHeaders(),
      }
    );
    const data = await response.json();
    if (!data.status)
      throw new Error(
        data.message || "Failed to fetch ai workflow creation sessions"
      );
    return data.data;
  }

  async getAIWorkflowCreationSession(
    aiWorkflowCreationSessionId: number,
    userId: string
  ): Promise<IAIWorkflowCreationSession> {
    const response = await fetch(
      `${this.getBaseUrl()}/builder-session/${aiWorkflowCreationSessionId}?user_id=${userId}`,
      {
        headers: this.getHeaders(),
      }
    );
    const data = await response.json();
    if (!data.status)
      throw new Error(
        data.message || "Failed to fetch ai workflow creation session"
      );
    return data.data;
  }

  async createAIWorkflowCreationSession(
    aiWorkflowCreationSessionData: Partial<IAIWorkflowCreationSession>,
    userId: string
  ): Promise<IAIWorkflowCreationSession> {
    const session = {
      ...aiWorkflowCreationSessionData,
      user_id: userId,
    };

    const response = await fetch(
      `${this.getBaseUrl()}/builder-session/?user_id=${userId}`,
      {
        method: "POST",
        headers: this.getHeaders(),
        body: JSON.stringify(session),
      }
    );

    let data;

    try {
      data = await response.json();
    } catch (err) {
      throw new Error(`Invalid JSON from server: ${err}`);
    }

    if (!response.ok) {
      throw new Error(
        data.message || "Failed to create ai workflow creation session"
      );
    }

    return data.data ?? data;
  }
}

export const aiWorkflowCreationAPI = new AIWorkflowCreationAPI();
