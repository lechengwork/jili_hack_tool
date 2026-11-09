// Read-only audit of original social UI code and the existing fixed capture.
const fs=require('fs'),path=require('path'),crypto=require('crypto'),vm=require('vm');
const dir=path.resolve(__dirname,'..');
const sourcePath=path.join(dir,'static/aviator/assets/Game224/index.95fb8.js');
const source=fs.readFileSync(sourcePath,'utf8');
const pb=require('../../545/runtime/node_modules/protobufjs/minimal');
const session=fs.readFileSync(path.join(dir,'current_session.txt'),'utf8').trim();
const frames=fs.readFileSync(path.join(session,'frames.jsonl'),'utf8').trim().split('\n').map(JSON.parse);
const counts={};let bestHistory=[];
const mod={exports:{}};
vm.runInNewContext('('+fs.readFileSync(path.join(__dirname,'fastProto.factory.js'),'utf8')+')',{String,Number,Array})({},n=>{if(n!=='protobufjs/minimal')throw Error(n);return pb},mod);
for(const frame of frames){const r=pb.Reader.create(Buffer.from(frame.hex,'hex'));let cmd=0,payload=Buffer.alloc(0);while(r.pos<r.len){const t=r.uint32();if(t===8)cmd=r.uint32();else if(t===18)payload=r.bytes();else r.skipType(t&7)}const key=frame.dir+':'+cmd;counts[key]=(counts[key]||0)+1;if(frame.dir==='RECV'&&cmd===42){const C=mod.exports.fastProto.FastWinList,d=C.decode(payload);if(!Buffer.from(C.encode(d).finish()).equals(payload))throw Error('Best history original-codec roundtrip failed');bestHistory.push({seq:frame.seq,payload_bytes:payload.length,entries:d.list.length,original_codec_byte_roundtrip:true})}}
const markers=[
 ['local_simulated_players','i.create=function(e){for(var t=0;t<220;',310],
 ['local_random_names','t.init=function(e,t,i,r){if(this.aid=e+1',450],
 ['local_cashout','t.checkRate=function(e,t)',350],
 ['local_bet_amounts','t.setBaseBet=function()',350],
 ['online_probability_by_local_hour','i.calcAlive=function()',250],
 ['displayed_player_count_is_row_count','i.updateTotalPlayer=function()',160],
 ['displayed_total_bet_is_local_sum','i.updateTotalBet=function(e)',230],
 ['initial_24_history_values_are_local_random','i.getRoomInfo=function(){for(var e=0;e<24;',700],
 ['later_history_uses_server_settlement','Game.uiCtrl.addHistory(e.endRate)',170],
 ['main_rank_request_goes_to_server','i.rankReq=function(){node$1.send',180],
 ['main_rank_response_goes_to_ui','case r.S2U_Rank:',220],
 ['main_rank_ui_uses_monthly_server_records','i.setRankboard=function(e)',390]
];
const evidence=markers.map(([claim,marker,length])=>{const offset=source.indexOf(marker);if(offset<0)throw Error('Missing original evidence: '+claim);return{claim,source_byte_offset:Buffer.byteLength(source.slice(0,offset)),excerpt:source.slice(offset,offset+length)}});
const report={scope:'Existing 2026-11-06 IDR capture and its original frontend; no new login or wager',source:path.relative(dir,sourcePath),source_sha256:crypto.createHash('sha256').update(source).digest('hex'),raw_frames:frames.length,main_rank_requests:counts['SEND:12']||0,main_rank_responses:counts['RECV:14']||0,best_history_responses:bestHistory,findings:{simulated_player_objects:220,initial_locally_generated_history_values:24,main_rank_origin:'Server response, not the KageBody player generator; no response in this capture',main_rank_human_accounts:'Not established',shared_multiplayer_crash_outcome:'Not established; a second simultaneous session would be needed to compare outcomes',own_wager_settlement:'Server supplied; already verified by the game-specific adapter',single_player_with_social_simulation:'Consistent with observed client-controlled round lifecycle and local social simulation; not a proof about all other sessions'},evidence};
fs.writeFileSync(path.join(__dirname,'social_audit.json'),JSON.stringify(report,null,2)+'\n');
console.log(JSON.stringify({raw_frames:report.raw_frames,simulated_player_objects:220,initial_local_history:24,main_rank_requests:report.main_rank_requests,main_rank_responses:report.main_rank_responses,best_history:bestHistory,evidence_assertions:evidence.length}));
