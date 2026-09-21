import React, { useState } from "react";
import { Alert, Button, Card, Form, Select, Typography, Upload } from "antd";
import { InboxOutlined } from "@ant-design/icons";
import { useNavigate } from "react-router-dom";
import { apiClient, friendlyError } from "../api/client.js";

const { Dragger } = Upload;

export default function DuplicateTldCheckPage() {
  const navigate = useNavigate();
  const [uploadResult, setUploadResult] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [starting, setStarting] = useState(false);
  const [error, setError] = useState(null);
  const [form] = Form.useForm();

  async function handleUpload(file) {
    setUploading(true);
    setError(null);
    const formData = new FormData();
    formData.append("file", file);
    try {
      const { data } = await apiClient.post("/api/jobs/upload?job_type=DUPLICATE_CHECK", formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      setUploadResult(data);
      form.setFieldsValue({
        email_column: data.detected_email_columns.length === 1 ? data.detected_email_columns[0] : undefined,
      });
    } catch (err) {
      setError(friendlyError(err, "Upload failed."));
    } finally {
      setUploading(false);
    }
    return false;
  }

  async function handleStart(values) {
    setStarting(true);
    setError(null);
    try {
      await apiClient.post(`/api/jobs/${uploadResult.job_id}/start`, {
        email_column: values.email_column,
        toggles: {
          allowed_tld: true,
          invalid_email: true,
          duplicate_email: true,
          duplicate_vs_master: true,
          personal_email: false,
          restricted_domain: false,
          restricted_keyword: false,
          restricted_title: false,
          restricted_industry: false,
          one_character_username: false,
          numeric_username: false,
          username_equals_domain: false,
          spam_domain: false,
        },
        merge_to_master: false,
      });
      navigate(`/jobs/${uploadResult.job_id}`);
    } catch (err) {
      setError(friendlyError(err, "Could not start the check."));
    } finally {
      setStarting(false);
    }
  }

  const headerOptions = (uploadResult?.headers || []).map((h) => ({ label: h, value: h }));

  return (
    <div>
      <Typography.Title level={3}>Duplicate / TLD Check</Typography.Title>
      <Typography.Paragraph type="secondary">
        Checks a file for in-file duplicate emails, duplicates against the existing Master dataset, and separates
        Other-TLD records -- without applying the full restricted-domain/keyword/title pipeline and without merging
        anything into Master.
      </Typography.Paragraph>
      {error && <Alert type="error" message={error} style={{ marginBottom: 16 }} />}

      {!uploadResult && (
        <Card>
          <Dragger multiple={false} accept=".csv,.xlsx,.xlsm" beforeUpload={handleUpload} disabled={uploading} showUploadList={false}>
            <p className="ant-upload-drag-icon">
              <InboxOutlined />
            </p>
            <p>Click or drag a CSV or Excel file to check</p>
          </Dragger>
        </Card>
      )}

      {uploadResult && (
        <Card title={`File: ${uploadResult.file_name}`}>
          <Form form={form} layout="vertical" onFinish={handleStart}>
            <Form.Item name="email_column" label="Email Column" rules={[{ required: true }]}>
              <Select options={headerOptions} showSearch style={{ maxWidth: 320 }} />
            </Form.Item>
            <Button type="primary" htmlType="submit" loading={starting}>
              Run Check
            </Button>
          </Form>
        </Card>
      )}
    </div>
  );
}
