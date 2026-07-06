export interface SimMessage {
  event_id: string;
  text: string;
  sender: string;
  created_at: string | null;
  is_system_msg: boolean;
  project_id: string | null;
  project_name: string | null;
  customer: string | null;
  skills: string[];
  status: string | null;
  mentioned_name: string | null;
  claimed_by_resource_id: string | null;
  claimed_by_name: string | null;
}

export interface Project {
  project_id: string;
  name: string;
  customer: string;
  status: string;
  type: string | null;
  priority: string | null;
  start_date: string | null;
  end_date: string | null;
  progress_percent: number;
  description: string | null;
  source: string;
  required_skills: string[];
  manager: string | null;
  practice: string | null;
  assigned_to: string;
  assignments?: Assignment[];
}

export interface Resource {
  resource_id: string;
  name: string;
  email: string | null;
  availability: string;
  utilization: number;
}

export interface Assignment {
  assignment_id: string;
  project_id: string;
  project_name: string | null;
  resource_id: string;
  resource_name: string | null;
  role: string | null;
  status: string;
  progress_percent: number;
}
