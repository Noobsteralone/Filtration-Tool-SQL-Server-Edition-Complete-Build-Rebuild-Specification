import React, { useEffect, useState } from "react";
import { Alert, Button, Card, Form, Input, Modal, Select, Switch, Table, Tag, Typography, message } from "antd";
import { PlusOutlined } from "@ant-design/icons";
import { apiClient, friendlyError } from "../api/client.js";

const ROLE_OPTIONS = [
  { label: "User", value: "USER" },
  { label: "Admin", value: "ADMIN" },
  { label: "Super Admin", value: "SUPER_ADMIN" },
];

export default function UsersPage() {
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [createOpen, setCreateOpen] = useState(false);
  const [form] = Form.useForm();

  function load() {
    setLoading(true);
    apiClient
      .get("/api/users")
      .then((res) => setUsers(res.data))
      .catch((err) => setError(friendlyError(err, "Could not load users.")))
      .finally(() => setLoading(false));
  }

  useEffect(load, []);

  async function createUser(values) {
    try {
      await apiClient.post("/api/users", values);
      message.success("User created.");
      setCreateOpen(false);
      form.resetFields();
      load();
    } catch (err) {
      message.error(friendlyError(err, "Could not create user."));
    }
  }

  async function toggleActive(user) {
    try {
      await apiClient.put(`/api/users/${user.UserID}`, { is_active: !user.IsActive });
      load();
    } catch (err) {
      message.error(friendlyError(err, "Could not update user."));
    }
  }

  return (
    <div>
      <Typography.Title level={3}>Users</Typography.Title>
      {error && <Alert type="error" message={error} style={{ marginBottom: 16 }} />}
      <Card
        loading={loading}
        extra={
          <Button icon={<PlusOutlined />} type="primary" onClick={() => setCreateOpen(true)}>
            New User
          </Button>
        }
      >
        <Table
          rowKey="UserID"
          dataSource={users}
          columns={[
            { title: "Username", dataIndex: "Username" },
            { title: "Email", dataIndex: "Email" },
            { title: "Role", dataIndex: "RoleName", render: (r) => <Tag>{r}</Tag> },
            {
              title: "Active",
              dataIndex: "IsActive",
              render: (active, record) => <Switch checked={active} onChange={() => toggleActive(record)} />,
            },
          ]}
        />
      </Card>

      <Modal title="New User" open={createOpen} onCancel={() => setCreateOpen(false)} onOk={() => form.submit()}>
        <Form form={form} layout="vertical" onFinish={createUser}>
          <Form.Item name="username" label="Username" rules={[{ required: true }]}>
            <Input />
          </Form.Item>
          <Form.Item name="email" label="Email" rules={[{ required: true, type: "email" }]}>
            <Input />
          </Form.Item>
          <Form.Item name="password" label="Password" rules={[{ required: true, min: 8 }]}>
            <Input.Password />
          </Form.Item>
          <Form.Item name="role_name" label="Role" initialValue="USER" rules={[{ required: true }]}>
            <Select options={ROLE_OPTIONS} />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
}
