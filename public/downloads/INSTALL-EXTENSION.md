# Install Thread for Chrome or Edge

1. Extract the whole extension ZIP. Keep the folder together.
2. Open `chrome://extensions` (Chrome) or `edge://extensions` (Edge).
3. Enable **Developer mode**.
4. Click **Load unpacked** and choose the inner folder containing `manifest.json`.
5. Pin Thread from the browser's Extensions menu.

Select text on a normal web page, click the extension, then **Save selected text**. Or right-click a selection and choose **Save selection to Thread**. Open the workspace and use **From your reading** to add a clip. The full app is bundled and works without a server or account.

Chrome/Edge desktop only. This is an unpacked developer extension, not a Chrome Web Store listing. Managed school devices may disallow Developer mode. Browser settings, protected store pages, and some PDF viewers cannot be clipped. A failed capture is shown as an error, not reported as saved.

## Permissions and data

- `activeTab`: temporary access after you invoke the extension.
- `scripting`: reads selected text, page title, and URL when you click capture.
- `storage`: keeps clips on this browser profile.
- `contextMenus`: adds a selection-only save action.

No host wildcard, browsing-history permission, remote scripts, analytics, or server upload. At most 100 clips, up to 20,000 characters each. Clip titles and URLs are saved as provenance. The app workspace uses browser local storage; the reading inbox uses extension local storage. They are separate from data in the hosted website. Export backups to transfer work.

To update, replace the files and click Reload on the extensions page. To uninstall, click Remove; export your workspace first. Uninstalling or clearing browser storage may erase work.
