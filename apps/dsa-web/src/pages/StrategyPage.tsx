import type React from 'react';
import { useCallback, useEffect, useState } from 'react';
import { ApiErrorAlert, Button, EmptyState, PageHeader } from '../components/common';
import { listStrategies, uploadStrategy, deleteStrategy } from '../api/strategy';
import type { StrategyInfo } from '../types/strategy';
import type { ParsedApiError } from '../api/error';
import { getParsedApiError } from '../api/error';



const ACCEPTED_FILE_TYPES = ['.pdf', '.doc', '.docx', '.txt', '.png', '.jpg', '.jpeg', '.bmp', '.gif'];
const ACCEPTED_EXTENSIONS = ACCEPTED_FILE_TYPES.join(',');

export default function StrategyPage() {
  const [strategies, setStrategies] = useState<StrategyInfo[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<ParsedApiError | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadName, setUploadName] = useState('');
  const [uploadDescription, setUploadDescription] = useState('');
  const [isDeleting, setIsDeleting] = useState<string | null>(null);
  const [toast, setToast] = useState<string | null>(null);

  const showToast = useCallback((message: string) => {
    setToast(message);
    setTimeout(() => setToast(null), 3000);
  }, []);

  const loadStrategies = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const response = await listStrategies();
      setStrategies(response.strategies);
    } catch (e) {
      setError(getParsedApiError(e));
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadStrategies();
  }, [loadStrategies]);

  const handleFileSelect = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    event.target.value = '';

    if (!file) return;

    setIsUploading(true);
    setError(null);

    try {
      await uploadStrategy({
        file,
        name: uploadName || undefined,
        description: uploadDescription || undefined,
      });
      showToast('策略上传成功');
      setUploadName('');
      setUploadDescription('');
      await loadStrategies();
    } catch (e) {
      setError(getParsedApiError(e));
    } finally {
      setIsUploading(false);
    }
  };

  const handleDelete = async (strategyId: string) => {
    setIsDeleting(strategyId);
    setError(null);

    try {
      await deleteStrategy(strategyId);
      showToast('策略删除成功');
      await loadStrategies();
    } catch (e) {
      setError(getParsedApiError(e));
    } finally {
      setIsDeleting(null);
    }
  };

  const formatFileType = (fileType: string) => {
    const typeMap: Record<string, string> = {
      '.pdf': 'PDF',
      '.doc': 'Word',
      '.docx': 'Word',
      '.txt': '文本',
      '.png': '图片',
      '.jpg': '图片',
      '.jpeg': '图片',
      '.bmp': '图片',
      '.gif': '图片',
    };
    return typeMap[fileType] || fileType;
  };

  return (
    <div className="min-h-screen bg-base">
      <PageHeader title="策略管理" description="上传和管理股票分析策略文件" />

      <div className="mx-auto max-w-4xl px-4 py-6">
        {error && (
          <div className="mb-6">
            <ApiErrorAlert error={error} />
          </div>
        )}

        {toast && (
          <div className="fixed bottom-4 right-4 z-50 rounded-lg bg-green-600 px-4 py-2 text-white shadow-lg">
            {toast}
          </div>
        )}

        <div className="card mb-6">
          <h2 className="mb-4 text-lg font-semibold">上传策略</h2>
          <p className="mb-4 text-sm text-base-content/60">
            支持的文件格式：PDF、Word (.doc/.docx)、文本 (.txt)、图片 (.png/.jpg/.jpeg/.bmp/.gif)
          </p>

          <div className="mb-4 grid gap-4 sm:grid-cols-2">
            <input
              type="text"
              placeholder="策略名称（可选，默认使用文件名）"
              value={uploadName}
              onChange={(e) => setUploadName(e.target.value)}
              className="input input-bordered"
            />
            <input
              type="text"
              placeholder="策略描述（可选）"
              value={uploadDescription}
              onChange={(e) => setUploadDescription(e.target.value)}
              className="input input-bordered"
            />
          </div>

          <label className="btn btn-primary cursor-pointer disabled:btn-disabled">
            {isUploading ? (
              <>
                <span className="loading loading-spinner loading-sm" />
                上传中...
              </>
            ) : (
              '选择文件'
            )}
            <input
              type="file"
              accept={ACCEPTED_EXTENSIONS}
              onChange={handleFileSelect}
              disabled={isUploading}
              className="hidden"
            />
          </label>
        </div>

        <div className="card">
          <h2 className="mb-4 text-lg font-semibold">已上传的策略</h2>

          {isLoading ? (
            <div className="flex justify-center py-8">
              <span className="loading loading-spinner loading-lg" />
            </div>
          ) : strategies.length === 0 ? (
            <EmptyState
              title="暂无策略"
              description="上传你的第一个策略文件开始使用"
            />
          ) : (
            <div className="overflow-x-auto">
              <table className="table">
                <thead>
                  <tr>
                    <th>名称</th>
                    <th>类型</th>
                    <th>文档块数</th>
                    <th>上传时间</th>
                    <th>操作</th>
                  </tr>
                </thead>
                <tbody>
                  {strategies.map((strategy) => (
                    <tr key={strategy.id}>
                      <td>
                        <div className="font-medium">{strategy.name}</div>
                        {strategy.description && (
                          <div className="text-sm text-base-content/60">{strategy.description}</div>
                        )}
                      </td>
                      <td>
                        <span className="badge badge-ghost">
                          {formatFileType(strategy.file_type)}
                        </span>
                      </td>
                      <td>{strategy.chunk_count}</td>
                      <td className="text-sm text-base-content/60">
                        {new Date(strategy.created_at).toLocaleString('zh-CN')}
                      </td>
                      <td>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => void handleDelete(strategy.id)}
                          disabled={isDeleting === strategy.id}
                        >
                          {isDeleting === strategy.id ? (
                            <span className="loading loading-spinner loading-sm" />
                          ) : (
                            '删除'
                          )}
                        </Button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}