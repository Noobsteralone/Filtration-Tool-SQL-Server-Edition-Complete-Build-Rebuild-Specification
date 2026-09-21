import React, { useEffect, useState } from "react";
import { Alert, Button, Card, Input, Modal, Popconfirm, Space, Switch, Table, Tabs, Typography, message } from "antd";
import { PlusOutlined } from "@ant-design/icons";
import { apiClient, friendlyError } from "../api/client.js";

const LISTS = [
  { key: "personal-domains", label: "Personal Domains" },
  { key: "restricted-domains", label: "Restricted Domains" },
  { key: "spam-domains", label: "Spam Domains" },
  { key: "keywords", label: "Restricted Keywords" },
  { key: "titles", label: "Restricted Titles" },
  { key: "industries", label: "Restricted Industries" },
  { key: "allowed-tlds", label: "Allowed TLDs" },
];

function ReferenceListPanel({ segment }) {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [addOpen, setAddOpen] = useState(false);
  const [addValue, setAddValue] = useState("");
  const [bulkOpen, setBulkOpen] = useState(false);
  const [bulkValues, setBulkValues] = useState("");

  function load() {
    setLoading(true);
    apiClient
      .get(`/api/reference/${segment}`)
      .then((res) => setItems(res.data))
      .catch((err) => setError(friendlyError(err, "Could not load this list.")))
      .finally(() => setLoading(false));
  }

  useEffect(load, [segment]);

  async function addOne() {
    if (!addValue.trim()) return;
    try {
      await apiClient.post(`/api/reference/${segment}`, { value: addValue.trim(), is_active: true });
      setAddValue("");
      setAddOpen(false);
      load();
    } catch (err) {
      message.error(friendlyError(err, "Could not add entry."));
    }
  }

  async function addBulk() {
    const values = bulkValues
      .split(/[\n,]/)
      .map((v) => v.trim())
      .filter(Boolean);
    if (values.length === 0) return;
    try {
      const { data } = await apiClient.post(`/api/reference/${segment}/bulk`, { values });
      message.success(`Added ${data.added} new value(s).`);
      setBulkValues("");
      setBulkOpen(false);
      load();
    } catch (err) {
      message.error(friendlyError(err, "Could not bulk-add entries."));
    }
  }

  async function toggleActive(item) {
    try {
      await apiClient.put(`/api/reference/${segment}/${item.ID}`, { is_active: !item.IsActive });
      load();
    } catch (err) {
      message.error(friendlyError(err, "Could not update entry."));
    }
  }

  async function removeItem(id) {
    try {
      await apiClient.delete(`/api/reference/${segment}/${id}`);
      load();
    } catch (err) {
      message.error(friendlyError(err, "Could not delete entry."));
    }
  }

  return (
    <Card
      loading={loading}
      extra={
        <Space>
          <Button icon={<PlusOutlined />} onClick={() => setAddOpen(true)}>
            Add
          </Button>
          <Button onClick={() => setBulkOpen(true)}>Bulk Paste</Button>
          <Button href={`/api/reference/${segment}/export`} target="_blank">
            Export CSV
          </Button>
        </Space>
      }
    >
      {error && <Alert type="error" message={error} style={{ marginBottom: 16 }} />}
      <Table
        rowKey="ID"
        dataSource={items}
        columns={[
          { title: "Value", dataIndex: "Value" },
          {
            title: "Active",
            dataIndex: "IsActive",
            render: (active, record) => <Switch checked={active} onChange={() => toggleActive(record)} />,
          },
          {
            title: "Actions",
            render: (_, record) => (
              <Popconfirm title="Delete this entry?" onConfirm={() => removeItem(record.ID)}>
                <Button size="small" danger>
                  Delete
                </Button>
              </Popconfirm>
            ),
          },
        ]}
      />

      <Modal title="Add Entry" open={addOpen} onOk={addOne} onCancel={() => setAddOpen(false)}>
        <Input value={addValue} onChange={(e) => setAddValue(e.target.value)} onPressEnter={addOne} placeholder="e.g. example.com" />
      </Modal>

      <Modal title="Bulk Paste" open={bulkOpen} onOk={addBulk} onCancel={() => setBulkOpen(false)} width={600}>
        <Typography.Paragraph type="secondary">One value per line (or comma-separated). Duplicates are skipped.</Typography.Paragraph>
        <Input.TextArea rows={10} value={bulkValues} onChange={(e) => setBulkValues(e.target.value)} />
      </Modal>
    </Card>
  );
}

export default function ReferenceListsPage() {
  return (
    <div>
      <Typography.Title level={3}>Reference Lists</Typography.Title>
      <Tabs items={LISTS.map((l) => ({ key: l.key, label: l.label, children: <ReferenceListPanel segment={l.key} /> }))} />
    </div>
  );
}
