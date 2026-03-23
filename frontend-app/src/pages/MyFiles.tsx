import React, { useState, useCallback } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import { useFolderContents, useDeleteFile, useRenameFile, useMoveFile } from '../hooks/useFiles';
import { useCreateFolder, useBreadcrumb } from '../hooks/useFolders';
import { useUpload } from '../hooks/useUpload';
import { useDragDrop } from '../hooks/useDragDrop';
import { useSelection } from '../hooks/useSelection';
import { FileGrid } from '../components/files/FileGrid';
import { FileList } from '../components/files/FileList';
import { FileBreadcrumb } from '../components/files/FileBreadcrumb';
import { UploadButton } from '../components/upload/UploadButton';
import { UploadProgress } from '../components/upload/UploadProgress';
import { DropZone } from '../components/upload/DropZone';
import { NewFolderDialog } from '../components/upload/NewFolderDialog';
import { ViewToggle } from '../components/common/ViewToggle';
import { SortDropdown } from '../components/common/SortDropdown';
import { BulkActions } from '../components/common/BulkActions';
import { RenameDialog } from '../components/modals/RenameDialog';
import { DeleteConfirm } from '../components/modals/DeleteConfirm';
import { MoveDialog } from '../components/modals/MoveDialog';
import { ShareDialog } from '../components/sharing/ShareDialog';
import { TagManager } from '../components/modals/TagManager';
import { VersionHistory } from '../components/modals/VersionHistory';
import { FileContextMenu } from '../components/files/FileContextMenu';
import { useContextMenu } from '../hooks/useContextMenu';
import type { FileItem, ViewMode, SortField, SortOrder } from '../types/file';

export const MyFiles: React.FC = () => {
  const [params, setParams] = useSearchParams();
  const folderId = params.get('folder') || undefined;
  const navigate = useNavigate();
  const [view, setView] = useState<ViewMode>('grid');
  const [sortBy, setSortBy] = useState<SortField>('name');
  const [sortOrder, setSortOrder] = useState<SortOrder>('asc');
  const { data, isLoading } = useFolderContents(folderId, sortBy, sortOrder);
  const { data: breadcrumbs } = useBreadcrumb(folderId);
  const { uploads, uploadFiles, cancelUpload, clearCompleted } = useUpload();
  const selection = useSelection();
  const createFolder = useCreateFolder();
  const deleteFile = useDeleteFile();
  const renameFile = useRenameFile();
  const moveFile = useMoveFile();
  const contextMenu = useContextMenu();

  const [showNewFolder, setShowNewFolder] = useState(false);
  const [renameTarget, setRenameTarget] = useState<FileItem | null>(null);
  const [deleteTarget, setDeleteTarget] = useState<FileItem | null>(null);
  const [moveTarget, setMoveTarget] = useState<FileItem | null>(null);
  const [shareTarget, setShareTarget] = useState<FileItem | null>(null);
  const [tagTarget, setTagTarget] = useState<FileItem | null>(null);
  const [versionTarget, setVersionTarget] = useState<FileItem | null>(null);
  const [contextTarget, setContextTarget] = useState<FileItem | null>(null);

  const handleDrop = useCallback((files: File[]) => uploadFiles(files, folderId), [uploadFiles, folderId]);
  const { isDragging, handleDragEnter, handleDragLeave, handleDragOver, handleDrop: onDrop } = useDragDrop(handleDrop);

  const navigateToFolder = (id: string | null) => { if (id) setParams({ folder: id }); else setParams({}); selection.clearSelection(); };
  const openFile = (file: FileItem) => { if (file.is_folder) navigateToFolder(file.id); };
  const handleSort = (field: SortField) => { if (sortBy === field) setSortOrder((o) => (o === 'asc' ? 'desc' : 'asc')); else { setSortBy(field); setSortOrder('asc'); } };

  const files = data?.items || [];

  return (
    <div className="h-full flex flex-col" onDragEnter={handleDragEnter} onDragLeave={handleDragLeave} onDragOver={handleDragOver} onDrop={onDrop}>
      <DropZone isDragging={isDragging} />
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-4">
          {breadcrumbs && <FileBreadcrumb items={breadcrumbs} onNavigate={navigateToFolder} />}
          {!breadcrumbs && <h2 className="text-xl font-semibold text-gray-900 dark:text-white">My Files</h2>}
        </div>
        <div className="flex items-center gap-2">
          <SortDropdown value={sortBy} onChange={setSortBy} />
          <ViewToggle view={view} onChange={setView} />
          <UploadButton onUploadFiles={(f) => uploadFiles(f, folderId)} onNewFolder={() => setShowNewFolder(true)} />
        </div>
      </div>
      <BulkActions count={selection.count} onMove={() => setMoveTarget(files[0])} onDelete={() => setDeleteTarget(files[0])} onShare={() => {}} onTag={() => {}} onDownload={() => {}} onClear={selection.clearSelection} />
      <div className="flex-1 mt-4">
        {view === 'grid' ? (
          <FileGrid files={files} selectedIds={selection.selectedIds} onSelect={selection.select} onOpen={openFile} onContextMenu={(f, e) => { setContextTarget(f); contextMenu.open(e); }} isLoading={isLoading} />
        ) : (
          <FileList files={files} selectedIds={selection.selectedIds} onSelect={selection.select} onOpen={openFile} onContextMenu={(f, e) => { setContextTarget(f); contextMenu.open(e); }} sortBy={sortBy} sortOrder={sortOrder} onSort={handleSort} isLoading={isLoading} />
        )}
      </div>
      <UploadProgress uploads={uploads} onCancel={cancelUpload} onClearCompleted={clearCompleted} />
      <NewFolderDialog isOpen={showNewFolder} onClose={() => setShowNewFolder(false)} onCreate={(name) => createFolder.mutate({ name, parentId: folderId })} />
      {renameTarget && <RenameDialog isOpen={!!renameTarget} currentName={renameTarget.name} onClose={() => setRenameTarget(null)} onRename={(name) => renameFile.mutate({ id: renameTarget.id, name })} />}
      {deleteTarget && <DeleteConfirm isOpen={!!deleteTarget} itemName={deleteTarget.name} onClose={() => setDeleteTarget(null)} onConfirm={() => deleteFile.mutate(deleteTarget.id)} />}
      {moveTarget && <MoveDialog isOpen={!!moveTarget} onClose={() => setMoveTarget(null)} onMove={(fid) => moveFile.mutate({ id: moveTarget.id, targetFolderId: fid })} currentFolderId={folderId} />}
      {shareTarget && <ShareDialog isOpen={!!shareTarget} fileId={shareTarget.id} onClose={() => setShareTarget(null)} />}
      {tagTarget && <TagManager isOpen={!!tagTarget} fileId={tagTarget.id} onClose={() => setTagTarget(null)} />}
      {versionTarget && <VersionHistory isOpen={!!versionTarget} fileId={versionTarget.id} onClose={() => setVersionTarget(null)} />}
      {contextMenu.isOpen && contextTarget && (
        <FileContextMenu x={contextMenu.x} y={contextMenu.y} onClose={contextMenu.close} isFolder={contextTarget.is_folder}
          onOpen={() => openFile(contextTarget)} onDownload={() => window.open(`/api/files/${contextTarget.id}/download`)}
          onShare={() => setShareTarget(contextTarget)} onStar={() => {}} onTag={() => setTagTarget(contextTarget)}
          onMove={() => setMoveTarget(contextTarget)} onCopy={() => {}} onRename={() => setRenameTarget(contextTarget)}
          onTrash={() => setDeleteTarget(contextTarget)} onDetails={() => {}} onVersions={() => setVersionTarget(contextTarget)} />
      )}
    </div>
  );
};
