import React, { useEffect, useState } from "react";
import { Alert, Button, Card, Form, Input, Space, Table, Typography, message } from "antd";
import { apiClient, friendlyError } from "../api/client.js";

export default function SettingsPage() {
  const [settingsList, setSettingsList] = useState([]);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);
  const [editingKey, setEditingKey] = useState(null);
  const [form] = Form.useForm();

  function load() {
    setLoading(true);
    apiClient
      .get("/api/settings")
      .then((res) => setSettingsList(res.data))
      .catch((err) => setError(friendlyError(err, "Could not load settings.")))
      .finally(() => setLoading(false));
  }

  useEffect(load, []);

  async function save(key) {
    try {
      const value = form.getFieldValue(key);
      await apiClient.put(`/api/settings/${key}`, { value });
      message.success("Setting updated.");
      setEditingKey(null);
      load();
    } catch (err) {
      message.error(friendlyError(err, "Could not update setting."));
    }
  }

  return (
    <div>
      <Typography.Title level={3}>Settings</Typography.Title>
      {error && <Alert type="error" message={error} style={{ marginBottom: 16 }} />}
      <Card loading={loading}>
        <Form form={form}>
          <Table
            rowKey="SettingKey"
            dataSource={settingsList}
            pagination={false}
            columns={[
              { title: "Key", dataIndex: "SettingKey" },
              {
                title: "Value",
                dataIndex: "SettingValue",
                render: (value, record) =>
                  editingKey === record.SettingKey ? (
                    <Form.Item name={record.SettingKey} initialValue={value} style={{ margin: 0 }}>
                      <Input />
                    </Form.Item>
                  ) : (
                    <span>{value}</span>
                  ),
              },
              {
                title: "Actions",
                render: (_, record) =>
                  editingKey === record.SettingKey ? (
                    <Space>
                      <Button type="primary" size="small" onClick={() => save(record.SettingKey)}>
                        Save
                      </Button>
                      <Button size="small" onClick={() => setEditingKey(null)}>
                        Cancel
                      </Button>
                    </Space>
                  ) : (
                    <Button size="small" onClick={() => setEditingKey(record.SettingKey)}>
                      Edit
                    </Button>
                  ),
              },
            ]}
          />
        </Form>
      </Card>
    </div>
  );
}
