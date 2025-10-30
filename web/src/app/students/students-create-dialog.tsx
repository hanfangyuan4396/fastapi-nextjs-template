"use client";

import { useCallback, useState } from "react";
import { useTranslations } from "next-intl";

import { zodResolver } from "@hookform/resolvers/zod";
import { useForm } from "react-hook-form";
import { z } from "zod";

import { Button } from "@/components/ui/button";
import { Form, FormControl, FormField, FormItem, FormLabel, FormMessage } from "@/components/ui/form";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { createStudent } from "@/service/students";

// Schema 将在组件内部创建，以便使用翻译

export function CreateStudentDialog({ onCreated }: { onCreated?: () => void }) {
  const t = useTranslations();
  const [submitting, setSubmitting] = useState(false);

  // 创建带翻译的验证 schema
  const schema = z.object({
    name: z.string().min(1, t("validation.nameRequired")).max(100),
    gender: z.enum(["male", "female"] as const, { message: t("validation.genderRequired") }),
    student_id: z.string().min(1, t("validation.studentIdRequired")).max(50),
    age: z
      .union([z.string().length(0), z.coerce.number().int().min(0).max(200)])
      .optional()
      .transform((v) => (typeof v === "number" ? v : null)),
  });

  type FormValuesOutput = z.output<typeof schema>;
  type FormValuesInput = z.input<typeof schema>;

  const form = useForm<FormValuesInput, unknown, FormValuesOutput>({
    resolver: zodResolver(schema),
    defaultValues: { name: "", gender: undefined as unknown as "male" | "female", student_id: "", age: "" },
    mode: "onBlur",
  });

  const onSubmit = useCallback(async (values: FormValuesOutput) => {
    setSubmitting(true);
    try {
      const payload = {
        name: values.name,
        gender: values.gender,
        student_id: values.student_id,
        age: values.age ?? null,
      };
      const res = await createStudent(payload);
      if (res.code === 0) {
        form.reset();
        onCreated?.();
      }
    } finally {
      setSubmitting(false);
    }
  }, [form, onCreated]);

  return (
    <div className="flex items-center gap-3">
      <Form {...form}>
        <form onSubmit={form.handleSubmit(onSubmit)} className="flex flex-wrap items-end gap-3">
          <FormField
            control={form.control}
            name="name"
            render={({ field }) => (
              <FormItem>
                <FormLabel>{t("form.name")}</FormLabel>
                <FormControl>
                  <Input placeholder={t("form.namePlaceholder")} {...field} className="w-44" />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />

          <FormField
            control={form.control}
            name="student_id"
            render={({ field }) => (
              <FormItem>
                <FormLabel>{t("form.studentId")}</FormLabel>
                <FormControl>
                  <Input placeholder={t("form.studentIdPlaceholder")} {...field} className="w-44" />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />

          <FormField
            control={form.control}
            name="gender"
            render={({ field }) => (
              <FormItem>
                <FormLabel>{t("form.gender")}</FormLabel>
                <Select onValueChange={field.onChange} value={field.value}>
                  <FormControl>
                    <SelectTrigger className="w-32">
                      <SelectValue placeholder={t("form.genderPlaceholder")} />
                    </SelectTrigger>
                  </FormControl>
                  <SelectContent>
                    <SelectItem value="male">{t("table.male")}</SelectItem>
                    <SelectItem value="female">{t("table.female")}</SelectItem>
                  </SelectContent>
                </Select>
                <FormMessage />
              </FormItem>
            )}
          />

          <FormField
            control={form.control}
            name="age"
            render={({ field }) => (
              <FormItem>
                <FormLabel>{t("form.age")}</FormLabel>
                <FormControl>
                  <Input
                    placeholder={t("form.agePlaceholder")}
                    {...field}
                    value={field.value as string}
                    className="w-28"
                  />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />

          <Button type="submit" disabled={submitting}>{t("form.submit")}</Button>
        </form>
      </Form>
    </div>
  );
}
