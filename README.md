# TUS Card Reader

## Requirements

- [Rye](https://rye-up.com/)
- [libusb](https://libusb.info/)

## Installation

### Python environment

Ryeを使用して`pyproject.toml`で指定された依存関係をインストールします。

```sh
rye sync
```

次に仮想環境をアクティベートします。OSに応じて以下のいずれかのコマンドを実行してください。

#### Windows

```powershell
.venv\Scripts\activate
```

#### Unix/Linux

```sh
source .venv/bin/activate
```

### libusb

**WindowsではWinUSBとlibusbをインストールする必要があります。** インストール方法の詳細については、[nfcpyのドキュメント](https://nfcpy.readthedocs.io/en/latest/topics/get-started.html)を参照してください。

## Usage

実行する前に、NFCカードリーダーをUSB接続していることを確認してください。

以下のコマンドを実行してクライアントを起動します。

```sh
python src/main.py
```

環境変数`ENDPOINT_URL`を設定することで、読み取ったカードの情報を以下の形式でWebサーバーに送信(POST)できます。

```json
{
  "student_id": "1234567"
}
```

さらに環境変数`SUCCESS_SOUND_PATH`を設定することで、送信に成功した際に音声ファイルを再生できます。音声ファイルは[playsound](https://github.com/TaylorSMarks/playsound)でサポートされた形式である必要があります。
