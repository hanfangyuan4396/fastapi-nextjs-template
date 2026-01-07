import React from "react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { StudentsManagementClient } from "@/app/students-management/students-management-client";
import { renderWithIntl } from "../utils/render";
import { listStudents } from "@/service/students";

vi.mock("@/service/students", () => ({
  listStudents: vi.fn(),
}));

vi.mock("@/app/students-management/students-create-dialog", () => ({
  CreateStudentDialog: ({ onCreated }: { onCreated?: () => void }) => (
    <button type="button" onClick={onCreated}>
      mock-create
    </button>
  ),
}));

const buildStudent = (page: number) => ({
  id: page,
  name: `Student ${page}`,
  gender: "male" as const,
  age: 18,
  student_id: `S${page}`,
});

describe("StudentsManagementClient", () => {
  beforeEach(() => {
    vi.mocked(listStudents).mockReset();
  });

  it("loads data and paginates", async () => {
    vi.mocked(listStudents).mockImplementation(async (params) => {
      const page = params?.page ?? 1;
      return {
        code: 0,
        message: "",
        data: {
          items: [buildStudent(page)],
          page,
          page_size: 10,
          total: 12,
        },
      };
    });

    renderWithIntl(<StudentsManagementClient />);

    expect(await screen.findByText("Student 1")).toBeInTheDocument();
    expect(screen.getByText("共 12 条")).toBeInTheDocument();
    expect(vi.mocked(listStudents)).toHaveBeenCalledWith({ page: 1, page_size: 10 });

    const user = userEvent.setup();
    await user.click(screen.getByLabelText("Go to next page"));

    expect(await screen.findByText("Student 2")).toBeInTheDocument();
    expect(screen.getByText("第 2 / 2 页")).toBeInTheDocument();
    expect(vi.mocked(listStudents)).toHaveBeenCalledWith({ page: 2, page_size: 10 });
  });

  it("refreshes to page 1 after create", async () => {
    vi.mocked(listStudents).mockImplementation(async (params) => {
      const page = params?.page ?? 1;
      return {
        code: 0,
        message: "",
        data: {
          items: [buildStudent(page)],
          page,
          page_size: 10,
          total: 12,
        },
      };
    });

    renderWithIntl(<StudentsManagementClient />);
    expect(await screen.findByText("Student 1")).toBeInTheDocument();

    const user = userEvent.setup();
    await user.click(screen.getByLabelText("Go to next page"));
    expect(await screen.findByText("Student 2")).toBeInTheDocument();

    await user.click(screen.getByText("mock-create"));

    await waitFor(() => {
      expect(screen.getByText("第 1 / 2 页")).toBeInTheDocument();
    });
    expect(await screen.findByText("Student 1")).toBeInTheDocument();
  });
});
