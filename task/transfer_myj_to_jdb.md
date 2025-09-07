我之前在一些官方网站上（不是javdb.com）中爬取了一些影片的官方信息，现在我想把这些movie和actor信息整合到现在jdb数据库对应的collection中

现在myj的actress collection的数据形式如下：
{
_id: ObjectId('677061dd68b7cf2990f9b542'),
link: 'https://s1s1s1.com/actress/detail/6694',
japan_name: '相内リカ',
roman_name: 'AIUCHI RIKA',
publisher: 's1s1s1',
avatar: '6f6c471821a2c52cc89bd7c72e26874e:相内リカ_avatar.jpeg',
detail_parsed: true,
profile: {
'誕生日': '1987年12月11日',
'身長': '155cm',
'3サイズ': 'B95cm (H) W62cm H88cm',
'出身地': '東京都',
'血液型': 'O型',
'趣味': 'ダンス・I字バランス'
},
movies: [
{
link: 'https://s1s1s1.com/works/detail/SOE219?page_from=actress&sys_code=6799',
id: '6770ea3500a967ac390bae05',
movie_parsed: true,
parsed: true
},
{
link: 'https://s1s1s1.com/works/detail/SOE202?page_from=actress&sys_code=6799',
id: '6770ea3500a967ac390bae06',
movie_parsed: true,
parsed: true
},
{
link: 'https://s1s1s1.com/works/detail/SOE167?page_from=actress&sys_code=6799',
id: '6770ea3600a967ac390bae07',
movie_parsed: true,
parsed: true
},
{
link: 'https://s1s1s1.com/works/detail/SOE124?page_from=actress&sys_code=6799',
id: '6770ea3600a967ac390bae08',
movie_parsed: true,
parsed: true
},
{
link: 'https://s1s1s1.com/works/detail/SOE093?page_from=actress&sys_code=6799',
id: '6770ea3700a967ac390bae09',
movie_parsed: true,
parsed: true
},
{
link: 'https://s1s1s1.com/works/detail/SOE081?page_from=actress&sys_code=6799',
id: '6770ea3700a967ac390bae0a',
movie_parsed: true,
parsed: true
},
{
link: 'https://s1s1s1.com/works/detail/SOE062?page_from=actress&sys_code=6799',
id: '6770ea3800a967ac390bae0b',
movie_parsed: true,
parsed: true
},
{
link: 'https://s1s1s1.com/works/detail/SOE027?page_from=actress&sys_code=6799',
id: '6770ea3900a967ac390bae0c',
movie_parsed: true,
parsed: true
},
{
link: 'https://s1s1s1.com/works/detail/SOE007?page_from=actress&sys_code=6799',
id: '6770ea3900a967ac390bae0d',
movie_parsed: true,
parsed: true
},
{
link: 'https://s1s1s1.com/works/detail/ONED986?page_from=actress&sys_code=6799',
id: '6770ea3a00a967ac390bae0e',
movie_parsed: true,
parsed: true
},
{
link: 'https://s1s1s1.com/works/detail/ONED968?page_from=actress&sys_code=6799',
id: '6770ea3b00a967ac390bae0f',
movie_parsed: true,
parsed: true
}
],
movies_parsed: true,
profile_parsed: true,
avatar_parsed: true
}

对于jdb中的actor，你可以通过title中的名字来搜索，title可能包含逗号分隔的多个名字，只要其中一个能对应上myj中的japan_name就行。然后用myj中的数据更新jdb中的actor，更新的key主要是profile，japan_name,roman_name,publisher,link,movies改成official_movies更新到现有的doc中，已经查询过的在status中添加一个key，表示已经查询过/未查询到等状态，防止重复查询。

请在script/db中添加对应的脚本，注意使用tqdm表示更新的进度（只更新categories为censored的actor）和预估时间，并显示当前正在操作的记录的href和name