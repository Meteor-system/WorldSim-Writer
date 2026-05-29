import type { WorldCreateRequest } from '../api/types';

export type GenrePreset = WorldCreateRequest & {
  key: string;
  label: string;
  description: string;
};

export const GENRE_PRESETS: GenrePreset[] = [
  {
    key: 'fantasy',
    label: 'Fantasy',
    description: '王权、魔法与古老预言交织的群像奇幻。',
    title: '雾冠王国',
    genre_template: 'fantasy',
    truth_canon: '雾冠王国依靠三座古塔维持魔力潮汐。王室、边境骑士团与秘法学院都知道其中一座古塔已经失衡，但没人愿意公开承认。',
    tone_profile: { style: '史诗奇幻、阴谋暗线', pacing: '每章推进一个权力或魔法线索' },
    starter_assets: {
      characters: [
        {
          name: '艾琳·雾冠',
          role_type: 'protagonist',
          status: 'active',
          public_profile: { identity: '被流放的王女', skill: '古塔铭文解读' },
          hidden_traits: { secret: '她能听见第三座古塔的低语' },
          destiny_flag: '王国继承权争夺者',
          current_goals: ['查明古塔失衡真相'],
        },
        {
          name: '洛恩爵士',
          role_type: 'ally',
          status: 'active',
          public_profile: { identity: '边境骑士团指挥官', skill: '防线调度' },
          hidden_traits: { guilt: '曾参与驱逐艾琳' },
          destiny_flag: '摇摆盟友',
          current_goals: ['阻止北境魔物越过白墙'],
        },
      ],
      relations: [{ source_index: 0, target_index: 1, relation_type: 'strained_alliance', intensity: 3, visibility: 'public' }],
      foreshadows: [
        {
          title: '裂开的塔心石',
          description: '第三座古塔的塔心石出现了只有艾琳能看见的银色裂纹。',
          foreshadow_type: 'magic_clue',
          status: 'planted',
          urgency_level: 4,
          related_character_indexes: [0, 1],
          expected_resolution_window: '第3-6章',
        },
      ],
    },
  },
  {
    key: 'sci_fi',
    label: 'Sci-Fi',
    description: '边境殖民地、企业秩序与失控科技构成的太空悬疑。',
    title: '群星边境',
    genre_template: 'sci_fi',
    truth_canon: '人类边境殖民地依赖一座濒临失控的跃迁灯塔，企业安保、走私船团与殖民议会围绕灯塔控制权暗中角力。',
    tone_profile: { style: '冷峻太空歌剧', pacing: '高压悬疑' },
    starter_assets: {
      characters: [
        {
          name: '许砚',
          role_type: 'protagonist',
          status: 'active',
          public_profile: { identity: '灯塔维修工程师', skill: '跃迁阵列校准' },
          hidden_traits: { secret: '曾篡改灯塔事故日志' },
          destiny_flag: '灯塔核心密钥持有者',
          current_goals: ['查明灯塔异常脉冲来源'],
        },
        {
          name: '莱娜·周',
          role_type: 'rival',
          status: 'active',
          public_profile: { identity: '企业安保监察官', skill: '审讯与战术部署' },
          hidden_traits: { fear: '害怕边境全面断航' },
          destiny_flag: '企业命令执行者',
          current_goals: ['夺取灯塔维护权限'],
        },
      ],
      relations: [{ source_index: 0, target_index: 1, relation_type: 'mutual_suspicion', intensity: 3, visibility: 'private' }],
      foreshadows: [
        {
          title: '黑匣子脉冲',
          description: '每次跃迁灯塔校准失败后，废弃黑匣子都会收到一段来自未来的求救信号。',
          foreshadow_type: 'signal_clue',
          status: 'planted',
          urgency_level: 4,
          related_character_indexes: [0, 1],
          expected_resolution_window: '第3-5章',
        },
      ],
    },
  },
  {
    key: 'modern',
    label: 'Modern',
    description: '都市现实、人情债与隐藏利益网络驱动的现代剧情。',
    title: '霓虹旧账',
    genre_template: 'modern',
    truth_canon: '海城老工业区即将被改造成科技园，旧厂工人、地产集团与独立记者围绕一份二十年前的事故赔偿名单展开拉扯。',
    tone_profile: { style: '现实主义、克制悬疑', pacing: '以人物选择推动真相揭露' },
    starter_assets: {
      characters: [
        {
          name: '陈望',
          role_type: 'protagonist',
          status: 'active',
          public_profile: { identity: '独立调查记者', skill: '资料挖掘' },
          hidden_traits: { debt: '父亲曾在旧厂事故中沉默作证' },
          destiny_flag: '旧案揭露者',
          current_goals: ['找到事故赔偿名单原件'],
        },
        {
          name: '苏明岚',
          role_type: 'antagonist',
          status: 'active',
          public_profile: { identity: '地产集团项目负责人', skill: '危机公关' },
          hidden_traits: { weakness: '母亲是旧厂幸存者' },
          destiny_flag: '利益与亲情夹缝者',
          current_goals: ['确保科技园发布会顺利举行'],
        },
      ],
      relations: [{ source_index: 0, target_index: 1, relation_type: 'public_opponents', intensity: 4, visibility: 'public' }],
      foreshadows: [
        {
          title: '缺页赔偿名单',
          description: '陈望得到的名单复印件少了最后一页，而那一页可能写着真正的责任人。',
          foreshadow_type: 'document_clue',
          status: 'planted',
          urgency_level: 3,
          related_character_indexes: [0, 1],
          expected_resolution_window: '第2-4章',
        },
      ],
    },
  },
];

export function clonePreset(preset: GenrePreset): WorldCreateRequest {
  return JSON.parse(JSON.stringify({
    title: preset.title,
    genre_template: preset.genre_template,
    truth_canon: preset.truth_canon,
    tone_profile: preset.tone_profile,
    starter_assets: preset.starter_assets,
  })) as WorldCreateRequest;
}
