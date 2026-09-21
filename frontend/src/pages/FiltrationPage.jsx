import React, { useState } from "react";
import { Alert, Button, Card, Checkbox, Col, Form, Row, Select, Steps, Typography, Upload, message } from "antd";
import { InboxOutlined } from "@ant-design/icons";
import { useNavigate } from "react-router-dom";
import { apiClient, friendlyError } from "../api/client.js";
import { FILTER_TOGGLE_LABELS } from "../constants.js";

const { Dragger } = Upload;

const ALL_TOGGLE_KEYS = FILTER_TOGGLE_LABELS.map((t) => t.key);

function togglesArrayToObject(selectedKeys) {
  const selected = new Set(selectedKeys || []);
  return Object.fromEntries(ALL_TOGGLE_KEYS.map((key) => [key, selected.has(key)]));
}

export default function FiltrationPage() {
  const navigate = useNavigate();
  const [step, setStep] = useState(0);
  const [uploading, setUploading] = useState(false);
  const [starting, setStarting] = useState(false);
  const [error, setError] = useState(null);
  const [uploadResult, setUploadResult] = useState(null);
  const [form] = Form.useForm();

  async function handleUpload(file) {
    setUploading(true);
    setError(null);
    const formData = new FormData();
    formData.append("file", file);
    try {
      const { data } = await apiClient.post("/api/jobs/upload?job_type=FILTRATION", formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      setUploadResult(data);
      const initialEmailColumn = data.detected_email_columns.length === 1 ? data.detected_email_columns[0] : undefined;
      form.setFieldsValue({
        email_column: initialEmailColumn,
        title_column: data.detected_roles.TITLE[0],
        industry_column: data.detected_roles.INDUSTRY[0],
        name_column: data.detected_roles.NAME[0],
        company_column: data.detected_roles.COMPANY[0],
        country_column: data.detected_roles.COUNTRY[0],
        linkedin_column: data.detected_roles.LINKEDIN[0],
        toggles: ALL_TOGGLE_KEYS,
        merge_to_master: true,
      });
      setStep(1);
    } catch (err) {
      setError(friendlyError(err, "Upload failed."));
    } finally {
      setUploading(false);
    }
    return false; // prevent antd's default upload behaviour
  }

  async function handleStart(values) {
    setStarting(true);
    setError(null);
    try {
      const payload = {
        email_column: values.email_column,
        title_column: values.title_column || null,
        industry_column: values.industry_column || null,
        name_column: values.name_column || null,
        company_column: values.company_column || null,
        country_column: values.country_column || null,
        linkedin_column: values.linkedin_column || null,
        toggles: togglesArrayToObject(values.toggles),
        merge_to_master: !!values.merge_to_master,
      };
      await apiClient.post(`/api/jobs/${uploadResult.job_id}/start`, payload);
      message.success("Filtration job started.");
      navigate(`/jobs/${uploadResult.job_id}`);
    } catch (err) {
      setError(friendlyError(err, "Could not start the job."));
    } finally {
      setStarting(false);
    }
  }

  const headerOptions = (uploadResult?.headers || []).map((h) => ({ label: h, value: h }));
  const multipleEmailColumns = (uploadResult?.detected_email_columns || []).length > 1;

  return (
    <div>
      <Typography.Title level={3}>Filtration</Typography.Title>
      <Steps
        current={step}
        items={[{ title: "Upload File" }, { title: "Select Columns & Filters" }, { title: "Run" }]}
        style={{ marginBottom: 24, maxWidth: 700 }}
      />
      {error && <Alert type="error" message={error} style={{ marginBottom: 16 }} />}

      {step === 0 && (
        <Card>
          <Dragger multiple={false} accept=".csv,.xlsx,.xlsm" beforeUpload={handleUpload} disabled={uploading} showUploadList={false}>
            <p className="ant-upload-drag-icon">
              <InboxOutlined />
            </p>
            <p>Click or drag a CSV or Excel file to this area to upload</p>
            <p style={{ color: "#888" }}>Large files are streamed directly into SQL Server staging tables.</p>
          </Dragger>
        </Card>
      )}

      {step === 1 && uploadResult && (
        <Card title={`File: ${uploadResult.file_name}`}>
          {uploadResult.sheet_names && (
            <Alert
              type="info"
              style={{ marginBottom: 16 }}
              message={`Multi-sheet workbook detected: ${uploadResult.sheet_names.join(", ")}. All sheets will be combined.`}
            />
          )}
          {multipleEmailColumns && (
            <Alert
              type="warning"
              style={{ marginBottom: 16 }}
              message="Multiple possible e-mail columns were found. Please confirm which one to use."
            />
          )}
          <Form form={form} layout="vertical" onFinish={handleStart}>
            <Row gutter={16}>
              <Col span={8}>
                <Form.Item name="email_column" label="Email Column" rules={[{ required: true, message: "Required" }]}>
                  <Select options={headerOptions} placeholder="Select the e-mail column" showSearch />
                </Form.Item>
              </Col>
              <Col span={8}>
                <Form.Item name="title_column" label="Title Column (optional)">
                  <Select options={headerOptions} allowClear showSearch />
                </Form.Item>
              </Col>
              <Col span={8}>
                <Form.Item name="industry_column" label="Industry Column (optional)">
                  <Select options={headerOptions} allowClear showSearch />
                </Form.Item>
              </Col>
              <Col span={8}>
                <Form.Item name="name_column" label="Name Column (optional)">
                  <Select options={headerOptions} allowClear showSearch />
                </Form.Item>
              </Col>
              <Col span={8}>
                <Form.Item name="company_column" label="Company Column (optional)">
                  <Select options={headerOptions} allowClear showSearch />
                </Form.Item>
              </Col>
              <Col span={8}>
                <Form.Item name="country_column" label="Country Column (optional)">
                  <Select options={headerOptions} allowClear showSearch />
                </Form.Item>
              </Col>
            </Row>

            <Typography.Title level={5}>Processing Options</Typography.Title>
            <Form.Item name="toggles">
              <Checkbox.Group style={{ width: "100%" }}>
                <Row>
                  {FILTER_TOGGLE_LABELS.map((t) => (
                    <Col span={8} key={t.key} style={{ marginBottom: 8 }}>
                      <Checkbox value={t.key}>{t.label}</Checkbox>
                    </Col>
                  ))}
                </Row>
              </Checkbox.Group>
            </Form.Item>
            <Form.Item name="merge_to_master" valuePropName="checked">
              <Checkbox>Merge Kept records into the permanent Master dataset when finished</Checkbox>
            </Form.Item>

            <Button type="primary" htmlType="submit" loading={starting}>
              Start Filtration
            </Button>
          </Form>
        </Card>
      )}
    </div>
  );
}
