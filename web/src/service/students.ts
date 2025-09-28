import { httpGet, httpPost, type ApiResponse } from "./http";

export type Gender = "male" | "female";

export type Student = {
  id: number;
  name: string;
  gender: Gender;
  age: number | null;
  student_id: string;
};

export type StudentsListData = {
  items: Student[];
  page: number;
  page_size: number;
  total: number;
};

export type StudentsListResponse = ApiResponse<StudentsListData>;

export type ListStudentsParams = {
  page?: number;
  page_size?: number;
};

export async function listStudents(params: ListStudentsParams = {}): Promise<StudentsListResponse> {
  return httpGet<StudentsListData>("/students", params);
}

export type CreateStudentPayload = {
  name: string;
  gender: Gender;
  age?: number | null;
  student_id: string;
};

export type CreateStudentResponse = ApiResponse<Student>;

export async function createStudent(payload: CreateStudentPayload): Promise<CreateStudentResponse> {
  return httpPost<Student>("/students", payload);
}
