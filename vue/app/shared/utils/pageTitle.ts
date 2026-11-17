/** アプリ全体の名前。画面名がない画面（トップなど）のタブにはこれだけを出す */
export const APP_NAME = 'タスク管理';

/**
 * 画面ごとのタブ名。どのアプリのどの画面か区別できるよう、画面名の後ろにアプリ名を付ける
 */
export const pageTitle = (screen: string): string => `${screen} | ${APP_NAME}`;
